import py

from rpython.jit.metainterp.resume import Snapshot
from rpython.jit.metainterp.jitexc import JitException
from rpython.jit.metainterp.optimizeopt.unroll import optimize_unroll
from rpython.jit.metainterp.compile import ResumeAtLoopHeaderDescr
from rpython.jit.metainterp.history import (ConstInt, VECTOR, FLOAT, INT,
        BoxVector, TargetToken, JitCellToken, Box, PrimitiveTypeMixin)
from rpython.jit.metainterp.optimizeopt.optimizer import Optimizer, Optimization
from rpython.jit.metainterp.optimizeopt.util import make_dispatcher_method
from rpython.jit.metainterp.optimizeopt.dependency import (DependencyGraph, 
        MemoryRef, Scheduler, SchedulerData, Node)
from rpython.jit.metainterp.resoperation import (rop, ResOperation, GuardResOp)
from rpython.rlib.objectmodel import we_are_translated
from rpython.rlib.debug import debug_print, debug_start, debug_stop
from rpython.rlib.jit import Counters
from rpython.rtyper.lltypesystem import lltype, rffi

class NotAVectorizeableLoop(JitException):
    def __str__(self):
        return 'NotAVectorizeableLoop()'

def debug_print_operations(loop):
    if not we_are_translated():
        print('--- loop instr numbered ---')
        def ps(snap):
            if snap.prev is None:
                return []
            return ps(snap.prev) + snap.boxes[:]
        for i,op in enumerate(loop.operations):
            print "[",str(i).center(2," "),"]",op,
            if op.is_guard():
                if op.rd_snapshot is not None:
                    print ps(op.rd_snapshot)
                else:
                    print op.getfailargs()
            else:
                print ""

def optimize_vector(metainterp_sd, jitdriver_sd, loop, optimizations,
                    inline_short_preamble, start_state):
    optimize_unroll(metainterp_sd, jitdriver_sd, loop, optimizations,
                    inline_short_preamble, start_state, False)
    orig_ops = loop.operations
    try:
        metainterp_sd.profiler.count(Counters.OPT_VECTORIZE_TRY)
        opt = VectorizingOptimizer(metainterp_sd, jitdriver_sd, loop, optimizations)
        opt.propagate_all_forward()
        metainterp_sd.profiler.count(Counters.OPT_VECTORIZED)
    except NotAVectorizeableLoop:
        # vectorization is not possible, propagate only normal optimizations
        loop.operations = orig_ops

class VectorizingOptimizer(Optimizer):
    """ Try to unroll the loop and find instructions to group """

    def __init__(self, metainterp_sd, jitdriver_sd, loop, optimizations):
        Optimizer.__init__(self, metainterp_sd, jitdriver_sd, loop, optimizations)
        self.dependency_graph = None
        self.packset = None
        self.unroll_count = 0
        self.smallest_type_bytes = 0
        self.early_exit_idx = -1
        self.sched_data = None
        self.tried_to_pack = False

    def propagate_all_forward(self, clear=True):
        self.clear_newoperations()
        label = self.loop.operations[0]
        jump = self.loop.operations[-1]
        if jump.getopnum() not in (rop.LABEL, rop.JUMP):
            # compile_loop appends a additional label to all loops
            # we cannot optimize normal traces
            raise NotAVectorizeableLoop()

        self.linear_find_smallest_type(self.loop)
        byte_count = self.smallest_type_bytes
        vsize = self.metainterp_sd.cpu.vector_register_size
        if vsize == 0 or byte_count == 0 or label.getopnum() != rop.LABEL:
            # stop, there is no chance to vectorize this trace
            # we cannot optimize normal traces (if there is no label)
            raise NotAVectorizeableLoop()

        # find index guards and move to the earliest position
        self.analyse_index_calculations()
        if self.dependency_graph is not None:
            self.schedule() # reorder the trace

        # unroll
        self.unroll_count = self.get_unroll_count(vsize)
        self.unroll_loop_iterations(self.loop, self.unroll_count)
        self.loop.operations = self.get_newoperations();
        self.clear_newoperations();

        # vectorize
        self.build_dependency_graph()
        self.find_adjacent_memory_refs()
        self.extend_packset()
        self.combine_packset()
        self.schedule()

        self.collapse_index_guards()

    def emit_operation(self, op):
        if op.getopnum() == rop.DEBUG_MERGE_POINT:
            return
        self._last_emitted_op = op
        self._newoperations.append(op)

    def emit_unrolled_operation(self, op):
        self._last_emitted_op = op
        self._newoperations.append(op)

    def unroll_loop_iterations(self, loop, unroll_count):
        """ Unroll the loop X times. unroll_count is an integral how
        often to further unroll the loop.
        """

        op_count = len(loop.operations)

        label_op = loop.operations[0].clone()
        assert label_op.getopnum() == rop.LABEL
        jump_op = loop.operations[op_count-1]
        # use the target token of the label
        assert jump_op.getopnum() in (rop.LABEL, rop.JUMP)
        target_token = label_op.getdescr()
        if not we_are_translated():
            target_token.assumed_classes = {}
        if jump_op.getopnum() == rop.LABEL:
            jump_op = ResOperation(rop.JUMP, jump_op.getarglist(), None, target_token)
        else:
            jump_op = jump_op.clone()
            jump_op.setdescr(target_token)
        assert jump_op.is_final()

        self.emit_unrolled_operation(label_op)

        oi = 0
        pure = True
        operations = []
        ee_pos = -1
        ee_guard = None
        for i in range(1,op_count-1):
            op = loop.operations[i].clone()
            opnum = op.getopnum()
            if opnum == rop.GUARD_EARLY_EXIT:
                ee_pos = i
                ee_guard = op
            operations.append(op)
            self.emit_unrolled_operation(op)

        prohibit_opnums = (rop.GUARD_FUTURE_CONDITION, rop.GUARD_EARLY_EXIT,
                           rop.GUARD_NOT_INVALIDATED)

        orig_jump_args = jump_op.getarglist()[:]
        # it is assumed that #label_args == #jump_args
        label_arg_count = len(orig_jump_args)
        rename_map = {}
        for i in range(0, unroll_count):
            # fill the map with the renaming boxes. keys are boxes from the label
            for i in range(label_arg_count):
                la = label_op.getarg(i)
                ja = jump_op.getarg(i)
                if ja in rename_map:
                    ja = rename_map[ja]
                if la != ja:
                    rename_map[la] = ja
            #
            for oi, op in enumerate(operations):
                if op.getopnum() in prohibit_opnums:
                    continue # do not unroll this operation twice
                copied_op = op.clone()
                if copied_op.result is not None:
                    # every result assigns a new box, thus creates an entry
                    # to the rename map.
                    new_assigned_box = copied_op.result.clonebox()
                    rename_map[copied_op.result] = new_assigned_box
                    copied_op.result = new_assigned_box
                #
                args = copied_op.getarglist()
                for i, arg in enumerate(args):
                    try:
                        value = rename_map[arg]
                        copied_op.setarg(i, value)
                    except KeyError:
                        pass
                # not only the arguments, but also the fail args need
                # to be adjusted. rd_snapshot stores the live variables
                # that are needed to resume.
                if copied_op.is_guard():
                    assert isinstance(copied_op, GuardResOp)
                    target_guard = copied_op
                    if oi < ee_pos:
                        #self.clone_failargs(copied_op, ee_guard, rename_map)
                        pass
                    else:
                        self.clone_failargs(copied_op, copied_op, rename_map)
                #
                self.emit_unrolled_operation(copied_op)

        # the jump arguments have been changed
        # if label(iX) ... jump(i(X+1)) is called, at the next unrolled loop
        # must look like this: label(i(X+1)) ... jump(i(X+2))
        args = jump_op.getarglist()
        for i, arg in enumerate(args):
            try:
                value = rename_map[arg]
                jump_op.setarg(i, value)
            except KeyError:
                pass

        self.emit_unrolled_operation(jump_op)

    def clone_failargs(self, guard, target_guard, rename_map):
        snapshot = self.clone_snapshot(target_guard.rd_snapshot, rename_map)
        guard.rd_snapshot = snapshot
        if guard.getfailargs():
            args = target_guard.getfailargs()[:]
            for i,arg in enumerate(args):
                try:
                    value = rename_map[arg]
                    args[i] = value
                except KeyError:
                    pass
            guard.setfailargs(args)

    def clone_snapshot(self, snapshot, rename_map):
        # snapshots are nested like the MIFrames
        if snapshot is None:
            return None
        boxes = snapshot.boxes
        new_boxes = boxes[:]
        for i,box in enumerate(boxes):
            try:
                value = rename_map[box]
                new_boxes[i] = value
            except KeyError:
                pass

        snapshot = Snapshot(self.clone_snapshot(snapshot.prev, rename_map),
                            new_boxes)
        return snapshot

    def linear_find_smallest_type(self, loop):
        # O(#operations)
        for i,op in enumerate(loop.operations):
            if op.getopnum() == rop.GUARD_EARLY_EXIT:
                self.early_exit_idx = i
            if op.is_array_op():
                descr = op.getdescr()
                if not descr.is_array_of_pointers():
                    byte_count = descr.get_item_size_in_bytes()
                    if self.smallest_type_bytes == 0 \
                       or byte_count < self.smallest_type_bytes:
                        self.smallest_type_bytes = byte_count

    def get_unroll_count(self, simd_vec_reg_bytes):
        """ This is an estimated number of further unrolls """
        # this optimization is not opaque, and needs info about the CPU
        byte_count = self.smallest_type_bytes
        if byte_count == 0:
            return 0
        unroll_count = simd_vec_reg_bytes // byte_count
        return unroll_count-1 # it is already unrolled once

    def build_dependency_graph(self):
        self.dependency_graph = DependencyGraph(self.loop)

    def find_adjacent_memory_refs(self):
        """ the pre pass already builds a hash of memory references and the
        operations. Since it is in SSA form there are no array indices.
        If there are two array accesses in the unrolled loop
        i0,i1 and i1 = int_add(i0,c), then i0 = i0 + 0, i1 = i0 + 1.
        They are represented as a linear combination: i*c/d + e, i is a variable,
        all others are integers that are calculated in reverse direction"""
        loop = self.loop
        operations = loop.operations

        self.tried_to_pack = True

        self.packset = PackSet(self.dependency_graph, operations,
                               self.unroll_count,
                               self.smallest_type_bytes)
        graph = self.dependency_graph
        memory_refs = graph.memory_refs.items()
        # initialize the pack set
        for node_a,memref_a in memory_refs:
            for node_b,memref_b in memory_refs:
                if memref_a is memref_b:
                    continue
                # instead of compare every possible combination and
                # exclue a_opidx == b_opidx only consider the ones
                # that point forward:
                if node_a.is_before(node_b):
                    if memref_a.is_adjacent_to(memref_b):
                        if self.packset.can_be_packed(node_a, node_b):
                            pair = Pair(node_a,node_b)
                            pair.ptype = PackType.by_descr(node_a.getoperation().getdescr())
                            self.packset.packs.append(pair)

    def extend_packset(self):
        pack_count = self.packset.pack_count()
        while True:
            for pack in self.packset.packs:
                self.follow_use_defs(pack)
                self.follow_def_uses(pack)
            if pack_count == self.packset.pack_count():
                break
            pack_count = self.packset.pack_count()

    def follow_use_defs(self, pack):
        assert isinstance(pack, Pair)
        for ldep in pack.left.depends():
            for rdep in pack.right.depends():
                lnode = ldep.to
                rnode = rdep.to
                if lnode.is_before(rnode) and self.packset.can_be_packed(lnode, rnode):
                    savings = self.packset.estimate_savings(lnode, rnode, pack, False)
                    if savings >= 0:
                        self.packset.add_pair(lnode, rnode)

    def follow_def_uses(self, pack):
        assert isinstance(pack, Pair)
        savings = -1
        candidate = (None,None)
        for ldep in pack.left.provides():
            for rdep in pack.right.provides():
                lnode = ldep.to
                rnode = rdep.to
                if lnode.is_before(rnode) and \
                   self.packset.can_be_packed(lnode, rnode):
                    est_savings = \
                        self.packset.estimate_savings(lnode, rnode, pack, True)
                    if est_savings > savings:
                        savings = est_savings
                        candidate = (lnode, rnode)
        #
        if savings >= 0:
            assert candidate[0] is not None
            assert candidate[1] is not None
            self.packset.add_pair(candidate[0], candidate[1])

    def combine_packset(self):
        if len(self.packset.packs) == 0:
            raise NotAVectorizeableLoop()
        i = 0
        j = 0
        end_ij = len(self.packset.packs)
        while True:
            len_before = len(self.packset.packs)
            i = 0
            while i < end_ij:
                while j < end_ij and i < end_ij:
                    if i == j:
                        j += 1
                        continue
                    pack1 = self.packset.packs[i]
                    pack2 = self.packset.packs[j]
                    if pack1.rightmost_match_leftmost(pack2):
                        end_ij = self.packset.combine(i,j)
                    elif pack2.rightmost_match_leftmost(pack1):
                        end_ij = self.packset.combine(j,i)
                    j += 1
                j = 0
                i += 1
            if len_before == len(self.packset.packs):
                break

    def schedule(self):
        self.guard_early_exit = -1
        self.clear_newoperations()
        sched_data = VecScheduleData(self.metainterp_sd.cpu.vector_register_size)
        scheduler = Scheduler(self.dependency_graph, sched_data)
        while scheduler.has_more():
            position = len(self._newoperations)
            ops = scheduler.next(position)
            for op in ops:
                if self.tried_to_pack:
                    self.unpack_from_vector(op, sched_data)
                self.emit_operation(op)

        if not we_are_translated():
            for node in self.dependency_graph.nodes:
                assert node.emitted
        self.loop.operations = self._newoperations[:]
        self.clear_newoperations()

    def unpack_from_vector(self, op, sched_data):
        args = op.getarglist()
        for i, arg in enumerate(op.getarglist()):
            if isinstance(arg, Box):
                self._unpack_from_vector(args, i, arg, sched_data)
        if op.is_guard():
            fail_args = op.getfailargs()
            for i, arg in enumerate(fail_args):
                if arg and isinstance(arg, Box):
                    self._unpack_from_vector(fail_args, i, arg, sched_data)

    def _unpack_from_vector(self, args, i, arg, sched_data):
        arg = sched_data.unpack_rename(arg)
        args[i] = arg
        (j, vbox) = sched_data.box_to_vbox.get(arg, (-1, None))
        if vbox:
            arg_cloned = arg.clonebox()
            cj = ConstInt(j)
            ci = ConstInt(1)
            opnum = rop.VEC_FLOAT_UNPACK
            if vbox.item_type == INT:
                opnum = rop.VEC_INT_UNPACK
            unpack_op = ResOperation(opnum, [vbox, cj, ci], arg_cloned)
            self.emit_operation(unpack_op)
            sched_data.rename_unpacked(arg, arg_cloned)
            args[i] = arg_cloned

    def analyse_index_calculations(self):
        if len(self.loop.operations) <= 1 or self.early_exit_idx == -1:
            return

        self.dependency_graph = graph = DependencyGraph(self.loop)

        label_node = graph.getnode(0)
        ee_guard_node = graph.getnode(self.early_exit_idx)
        guards = graph.guards
        fail_args = []
        for guard_node in guards:
            if guard_node is ee_guard_node:
                continue
            del_deps = []
            pullup = []
            valid_trans = True
            last_prev_node = None
            for path in guard_node.iterate_paths(ee_guard_node, True):
                prev_node = path.second()
                if fail_args_break_dependency(guard_node, prev_node, ee_guard_node):
                    if prev_node == last_prev_node:
                        continue
                    del_deps.append((prev_node, guard_node))
                else:
                    if path.has_no_side_effects(exclude_first=True, exclude_last=True):
                        #index_guards[guard.getindex()] = IndexGuard(guard, path.path[:])
                        path.set_schedule_priority(10)
                        pullup.append(path.last_but_one())
                    else:
                        valid_trans = False
                        break
                last_prev_node = prev_node
            if valid_trans:
                for a,b in del_deps:
                    a.remove_edge_to(b)
                for lbo in pullup:
                    if lbo is ee_guard_node:
                        continue
                    ee_guard_node.remove_edge_to(lbo)
                    label_node.edge_to(lbo, label='pullup')
                # only the last guard needs a connection
                guard_node.edge_to(ee_guard_node, label='pullup-last-guard')
                guard_node.relax_guard_to(ee_guard_node)

    def collapse_index_guards(self):
        strongest_guards = {}
        strongest_guards_var = {}
        index_vars = self.dependency_graph.index_vars
        comparison_vars = self.dependency_graph.comparison_vars
        operations = self.loop.operations
        var_for_guard = {}
        for i in range(len(operations)-1, -1, -1):
            op = operations[i]
            if op.is_guard():
                for arg in op.getarglist():
                    var_for_guard[arg] = True
                    try:
                        comparison = comparison_vars[arg]
                        for index_var in list(comparison.getindex_vars()):
                            if not index_var:
                                continue
                            var = index_var.getvariable()
                            strongest_known = strongest_guards_var.get(var, None)
                            if not strongest_known:
                                strongest_guards_var[var] = index_var
                                continue
                            if index_var.less(strongest_known):
                                strongest_guards_var[var] = strongest_known
                                strongest_guards[op] = strongest_known
                    except KeyError:
                        pass

        last_op_idx = len(operations)-1
        for op in operations:
            if op.is_guard():
                stronger_guard = strongest_guards.get(op, None)
                if stronger_guard:
                    # there is a stronger guard
                    continue
                else:
                    self.emit_operation(op)
                    continue
            if op.is_always_pure() and op.result:
                try:
                    var_index = index_vars[op.result]
                    var_index.adapt_operation(op)
                except KeyError:
                    pass
            self.emit_operation(op)

        self.loop.operations = self._newoperations[:]

def must_unpack_result_to_exec(op, target_op):
    # TODO either move to resop or util
    if op.getoperation().vector != -1:
        return False
    return True

def fail_args_break_dependency(guard, prev_op, target_guard):
    failargs = guard.getfailarg_set()
    new_failargs = target_guard.getfailarg_set()

    op = prev_op.getoperation()
    if not op.is_always_pure(): # TODO has_no_side_effect():
        return True
    if op.result is not None:
        arg = op.result
        if arg not in failargs or \
               arg in failargs and arg in new_failargs:
            return False
    for arg in op.getarglist():
        if arg not in failargs or \
               arg in failargs and arg in new_failargs:
            return False
    # THINK about: increased index in fail arg, but normal index on arglist
    # this might be an indicator for edge removal
    return True

class PackType(PrimitiveTypeMixin):
    UNKNOWN_TYPE = '-'

    def __init__(self, type, size, signed):
        assert type in (FLOAT, INT, PackType.UNKNOWN_TYPE)
        self.type = type
        self.size = size
        self.signed = signed

    def gettype(self):
        return self.type

    def getsize(self):
        return self.size

    def getsigned(self):
        return self.signed

    def get_byte_size(self):
        return self.size

    @staticmethod
    def by_descr(descr):
        _t = INT
        if descr.is_array_of_floats() or descr.concrete_type == FLOAT:
            _t = FLOAT
        pt = PackType(_t, descr.get_item_size_in_bytes(), descr.is_item_signed())
        return pt

    def is_valid(self):
        return self.type != PackType.UNKNOWN_TYPE and self.size > 0

    def new_vector_box(self, count):
        return BoxVector(self.type, count, self.size, self.signed)

    def record_vbox(self, vbox):
        if self.type == PackType.UNKNOWN_TYPE:
            self.type = vbox.item_type
            assert self.type in (FLOAT, INT)
            self.signed = vbox.signed
        if vbox.item_size > self.size:
            self.size = vbox.item_size

    def __repr__(self):
        return 'PackType(%s, %s, %s)' % (self.type, self.size, self.signed)

    def clone(self):
        return PackType(self.type, self.size, self.signed)


class OpToVectorOp(object):
    def __init__(self, arg_ptypes, result_ptype, has_ptype=False, index=-1, result_vsize_arg=-1):
        self.arg_ptypes = arg_ptypes
        self.result_ptype = result_ptype
        self.has_ptype = has_ptype
        # TODO remove them?
        self.result = result_ptype != None
        self.result_vsize_arg = result_vsize_arg
        self.index = index

    def get_result_ptype(self):
        return self.result_ptype

    def get_arg_ptype(self, i):
        if i < 0 or i >= len(self.arg_ptypes):
            return None
        return self.arg_ptypes[i]

    def vector_arg(self, i):
        if i < 0 or i >= len(self.arg_ptypes):
            return False
        return self.arg_ptypes[i] is not None

PT_FLOAT = PackType(FLOAT, 4, False)
PT_DOUBLE = PackType(FLOAT, 8, False)
PT_INT_GENERIC = PackType(INT, -1, True)
PT_INT64 = PackType(INT, 8, True)
PT_FLOAT_GENERIC = PackType(INT, -1, True)
PT_GENERIC = PackType(PackType.UNKNOWN_TYPE, -1, True)

ROP_ARG_RES_VECTOR = {
    rop.VEC_INT_ADD:     OpToVectorOp((PT_INT_GENERIC, PT_INT_GENERIC), PT_INT_GENERIC),
    rop.VEC_INT_SUB:     OpToVectorOp((PT_INT_GENERIC, PT_INT_GENERIC), PT_INT_GENERIC),
    rop.VEC_INT_MUL:     OpToVectorOp((PT_INT_GENERIC, PT_INT_GENERIC), PT_INT_GENERIC),
    rop.VEC_INT_SIGNEXT: OpToVectorOp((PT_INT_GENERIC,), PT_INT_GENERIC, result_vsize_arg=1),

    rop.VEC_FLOAT_ADD:   OpToVectorOp((PT_FLOAT_GENERIC,PT_FLOAT_GENERIC), PT_FLOAT_GENERIC),
    rop.VEC_FLOAT_SUB:   OpToVectorOp((PT_FLOAT_GENERIC,PT_FLOAT_GENERIC), PT_FLOAT_GENERIC),
    rop.VEC_FLOAT_MUL:   OpToVectorOp((PT_FLOAT_GENERIC,PT_FLOAT_GENERIC), PT_FLOAT_GENERIC),
    rop.VEC_FLOAT_EQ:    OpToVectorOp((PT_FLOAT_GENERIC,PT_FLOAT_GENERIC), PT_INT_GENERIC),

    rop.VEC_RAW_LOAD:         OpToVectorOp((), PT_GENERIC, has_ptype=True),
    rop.VEC_GETARRAYITEM_RAW: OpToVectorOp((), PT_GENERIC, has_ptype=True),
    rop.VEC_RAW_STORE:        OpToVectorOp((None,None,PT_GENERIC,), None, has_ptype=True),
    rop.VEC_SETARRAYITEM_RAW: OpToVectorOp((None,None,PT_GENERIC,), None, has_ptype=True),

    rop.VEC_CAST_FLOAT_TO_SINGLEFLOAT: OpToVectorOp((PT_DOUBLE,), PT_FLOAT),
    # TODO remove index
    rop.VEC_CAST_SINGLEFLOAT_TO_FLOAT: OpToVectorOp((PT_FLOAT,), PT_DOUBLE, index=1),
    rop.VEC_CAST_FLOAT_TO_INT: OpToVectorOp((PT_DOUBLE,), PT_INT64),
    rop.VEC_CAST_INT_TO_FLOAT: OpToVectorOp((PT_INT64,), PT_DOUBLE),
}


class VecScheduleData(SchedulerData):
    def __init__(self, vec_reg_size):
        self.box_to_vbox = {}
        self.unpack_rename_map = {}
        self.preamble_ops = None
        self.expansion_byte_count = -1
        self.vec_reg_size = vec_reg_size
        self.pack_ops = -1
        self.pack_off = -1

    def unpack_rename(self, arg):
        return self.unpack_rename_map.get(arg, arg)

    def rename_unpacked(self, arg, argdest):
        self.unpack_rename_map[arg] = argdest

    def as_vector_operation(self, pack):
        op_count = len(pack.operations)
        assert op_count > 1
        self.pack = pack
        # properties that hold for the pack are:
        # + isomorphism (see func above)
        # + tight packed (no room between vector elems)
        if pack.ptype is None:
            self.propagate_ptype()

        self.preamble_ops = []
        if pack.is_overloaded(self.vec_reg_size):
            self.preamble_ops = []
            stride = pack.size_in_bytes() // self.vec_reg_size
            for i in range(0, op_count, stride):
                self.pack_off = i
                self.pack_ops = stride
                self._as_vector_op()
            return self.preamble_ops
        else:
            self.pack_off = 0
            self.pack_ops = op_count
            self._as_vector_op()
            return self.preamble_ops

    def _as_vector_op(self):
        op0 = self.pack.operations[self.pack_off].getoperation()
        assert op0.vector != -1
        args = op0.getarglist()[:]

        tovector = ROP_ARG_RES_VECTOR.get(op0.vector, None)
        if tovector is None:
            raise NotImplementedError("vecop map entry missing. trans: pack -> vop")

        if tovector.index != -1:
            args.append(ConstInt(self.pack_off))

        args.append(ConstInt(self.pack_ops))
        vop = ResOperation(op0.vector, args, op0.result, op0.getdescr())

        for i,arg in enumerate(args):
            arg_ptype = tovector.get_arg_ptype(i)
            if arg_ptype and tovector.has_ptype:
                arg_ptype = self.pack.ptype
            if arg_ptype is not None:
                if arg_ptype.size == -1:
                    arg_ptype = self.pack.ptype
                self.vector_arg(vop, i, arg_ptype)
        if tovector.result:
            self.vector_result(vop, tovector)

        self.preamble_ops.append(vop)

    def propagate_ptype(self):
        op0 = self.pack.operations[0].getoperation()
        tovector = ROP_ARG_RES_VECTOR.get(op0.vector, None)
        if tovector is None:
            raise NotImplementedError("vecop map entry missing. trans: pack -> vop")
        if tovector.has_ptype:
            assert False, "load/store must have ptypes attached from the descriptor"
        args = op0.getarglist()[:]
        res_ptype = tovector.get_result_ptype().clone()
        for i,arg in enumerate(args):
            if tovector.vector_arg(i):
                _, vbox = self.box_to_vbox.get(arg, (-1, None))
                if vbox is not None:
                    res_ptype.record_vbox(vbox)
                else:
                    # vbox of a variable/constant is not present here
                    pass
        self.pack.ptype = res_ptype

    def vector_result(self, vop, tovector):
        ops = self.pack.operations
        ptype = tovector.get_result_ptype().clone()
        if tovector.has_ptype:
            ptype = self.pack.ptype
        if ptype is not None:
            if ptype.size == -1:
                ptype.size = self.pack.ptype.size
            vbox = self.box_vector(ptype)
        else:
            vbox = self.box_vector(self.pack.ptype)
        if tovector.result_vsize_arg != -1:
            # vec_int_signext specifies the size in bytes on the
            # first argument.
            arg = vop.getarg(tovector.result_vsize_arg)
            assert isinstance(arg, ConstInt)
            vbox.item_size = arg.value
        #
        vop.result = vbox
        i = self.pack_off
        end = i + self.pack_ops
        while i < end:
            op = ops[i].getoperation()
            self.box_to_vbox[op.result] = (i, vbox)
            i += 1

    def box_vector(self, ptype):
        """ TODO remove this? """
        return BoxVector(ptype.type, self.pack_ops, ptype.size, ptype.signed)

    def vector_arg(self, vop, argidx, arg_ptype):
        ops = self.pack.operations
        _, vbox = self.box_to_vbox.get(vop.getarg(argidx), (-1, None))
        if not vbox:
            vbox = self.expand_box_to_vector_box(vop, argidx)
        # vbox is a primitive type mixin
        packable = self.vec_reg_size // arg_ptype.getsize()
        packed = vbox.item_count
        assert packed >= 0
        assert packable >= 0
        if packed < packable:
            # the argument is scattered along different vector boxes
            args = [op.getoperation().getarg(argidx) for op in ops]
            vbox = self._pack(vbox, packed, args, packable)
        elif packed > packable:
            # the argument has more items than the operation is able to process!
            vbox = self.unpack(vbox, self.pack_off, packable, arg_ptype)
            vbox = self.extend(vbox, arg_ptype)
        vop.setarg(argidx, vbox)
        return vbox

    def extend(self, vbox, arg_ptype):
        if vbox.item_count * vbox.item_size == self.vec_reg_size:
            return vbox
        size = arg_ptype.getsize()
        assert (vbox.item_count * size) == self.vec_reg_size
        opnum = rop.VEC_INT_SIGNEXT
        vbox_cloned = arg_ptype.new_vector_box(vbox.item_count)
        op = ResOperation(opnum, [vbox, ConstInt(size), ConstInt(vbox.item_count)], vbox_cloned)
        self.preamble_ops.append(op)
        return vbox_cloned

    def unpack(self, vbox, index, count, arg_ptype):
        vbox_cloned = vbox.clonebox()
        vbox_cloned.item_count = count
        opnum = rop.VEC_FLOAT_UNPACK
        if vbox.item_type == INT:
            opnum = rop.VEC_INT_UNPACK
        op = ResOperation(opnum, [vbox, ConstInt(index), ConstInt(count)], vbox_cloned)
        self.preamble_ops.append(op)
        return vbox_cloned

    def _pack(self, tgt_box, index, args, packable):
        """ If there are two vector boxes:
          v1 = [<empty>,<emtpy>,X,Y]
          v2 = [A,B,<empty>,<empty>]
          this function creates a box pack instruction to merge them to:
          v1/2 = [A,B,X,Y]
        """
        opnum = rop.VEC_FLOAT_PACK
        if tgt_box.item_type == INT:
            opnum = rop.VEC_INT_PACK
        arg_count = len(args)
        i = index
        while i < arg_count and tgt_box.item_count < packable:
            arg = args[i]
            pos, src_box = self.box_to_vbox.get(arg, (-1, None))
            if pos == -1:
                i += 1
                continue
            new_box = tgt_box.clonebox()
            new_box.item_count += src_box.item_count
            op = ResOperation(opnum, [tgt_box, src_box, ConstInt(i),
                                      ConstInt(src_box.item_count)], new_box)
            self.preamble_ops.append(op)
            self._check_vec_pack(op)
            i += src_box.item_count

            # overwrite the new positions, arguments now live in new_box
            # at a new position
            for j in range(i):
                arg = args[j]
                self.box_to_vbox[arg] = (j, new_box)
        _, vbox = self.box_to_vbox.get(args[0], (-1, None))
        return vbox

    def _check_vec_pack(self, op):
        result = op.result
        arg0 = op.getarg(0)
        arg1 = op.getarg(1)
        index = op.getarg(2)
        count = op.getarg(3)
        assert isinstance(result, BoxVector)
        assert isinstance(arg0, BoxVector)
        assert isinstance(index, ConstInt)
        assert isinstance(count, ConstInt)
        assert arg0.item_size == result.item_size
        if isinstance(arg1, BoxVector):
            assert arg1.item_size == result.item_size
        else:
            assert count.value == 1
        assert index.value < result.item_size
        assert index.value + count.value <= result.item_size
        assert result.item_count > arg0.item_count

    def expand_box_to_vector_box(self, vop, argidx):
        arg = vop.getarg(argidx)
        all_same_box = True
        ops = self.pack.operations
        i = self.pack_off
        end = i + self.pack_ops
        while i < end:
            op = ops[i]
            if arg is not op.getoperation().getarg(argidx):
                all_same_box = False
                break
            i += 1

        box_type = arg.type
        if isinstance(arg, BoxVector):
            box_type = arg.item_type
        expand_opnum = rop.VEC_FLOAT_EXPAND
        if box_type == INT:
            expand_opnum = rop.VEC_INT_EXPAND

        # TODO
        vbox = BoxVector(box_type, self.pack_ops)
        if all_same_box:
            expand_op = ResOperation(expand_opnum, [arg], vbox)
            self.preamble_ops.append(expand_op)
        else:
            resop = ResOperation(rop.VEC_BOX, [ConstInt(self.pack_ops)], vbox)
            self.preamble_ops.append(resop)
            opnum = rop.VEC_FLOAT_PACK
            if arg.type == INT:
                opnum = rop.VEC_INT_PACK
            for i,op in enumerate(ops):
                arg = op.getoperation().getarg(argidx)
                resop = ResOperation(opnum,
                                     [vbox,ConstInt(i),arg], None)
                self.preamble_ops.append(resop)
        return vbox

def isomorphic(l_op, r_op):
    """ Same instructions have the same operation name.
    TODO what about parameters?
    """
    if l_op.getopnum() == r_op.getopnum():
        return True
    return False


class PackSet(object):

    def __init__(self, dependency_graph, operations, unroll_count,
                 smallest_type_bytes):
        self.packs = []
        self.dependency_graph = dependency_graph
        self.operations = operations
        self.unroll_count = unroll_count
        self.smallest_type_bytes = smallest_type_bytes

    def pack_count(self):
        return len(self.packs)

    def add_pair(self, l, r):
        p = Pair(l,r)
        self.packs.append(p)

    def can_be_packed(self, lnode, rnode):
        if isomorphic(lnode.getoperation(), rnode.getoperation()):
            if lnode.independent(rnode):
                for pack in self.packs:
                    if pack.left == lnode or \
                       pack.right == rnode:
                        return False
                return True
        return False

    def estimate_savings(self, lnode, rnode, pack, expand_forward):
        """ Estimate the number of savings to add this pair.
        Zero is the minimum value returned. This should take
        into account the benefit of executing this instruction
        as SIMD instruction.
        """
        savings = -1

        lpacknode = pack.left
        if self.prohibit_packing(lpacknode.getoperation(), lnode.getoperation()):
            return -1
        rpacknode = pack.right
        if self.prohibit_packing(rpacknode.getoperation(), rnode.getoperation()):
            return -1

        if not expand_forward:
            if not must_unpack_result_to_exec(lpacknode, lnode) and \
               not must_unpack_result_to_exec(rpacknode, rnode):
                savings += 1
        else:
            if not must_unpack_result_to_exec(lpacknode, lnode) and \
               not must_unpack_result_to_exec(rpacknode, rnode):
                savings += 1

        return savings

    def prohibit_packing(self, packed, inquestion):
        if inquestion.vector == -1:
            return True
        if packed.is_array_op():
            if packed.getarg(1) == inquestion.result:
                return True
        return False


    def combine(self, i, j):
        """ combine two packs. it is assumed that the attribute self.packs
        is not iterated when calling this method. """
        pack_i = self.packs[i]
        pack_j = self.packs[j]
        pack_i.clear()
        pack_j.clear()
        operations = pack_i.operations
        for op in pack_j.operations[1:]:
            operations.append(op)
        self.packs[i] = pack = Pack(operations)
        pack.ptype = pack_i.ptype

        # instead of deleting an item in the center of pack array,
        # the last element is assigned to position j and
        # the last slot is freed. Order of packs doesn't matter
        last_pos = len(self.packs) - 1
        if j == last_pos:
            del self.packs[j]
        else:
            self.packs[j] = self.packs[last_pos]
            del self.packs[last_pos]
        return last_pos

    def pack_for_operation(self, node):
        for pack in self.packs:
            for node2 in pack.operations:
                if node == node2:
                    return pack
        return None

class Pack(object):
    """ A pack is a set of n statements that are:
        * isomorphic
        * independent
    """
    def __init__(self, ops):
        self.operations = ops
        self.savings = 0
        self.ptype = None
        for node in self.operations:
            node.pack = self

    def clear(self):
        for node in self.operations:
            node.pack = None

    def rightmost_match_leftmost(self, other):
        assert isinstance(other, Pack)
        rightmost = self.operations[-1]
        leftmost = other.operations[0]
        return rightmost == leftmost

    def size_in_bytes(self):
        return self.ptype.get_byte_size() * len(self.operations)

    def is_overloaded(self, vec_reg_byte_size):
        size = self.size_in_bytes()
        return size > vec_reg_byte_size

    def __repr__(self):
        return "Pack(%r)" % self.operations

class Pair(Pack):
    """ A special Pack object with only two statements. """
    def __init__(self, left, right):
        assert isinstance(left, Node)
        assert isinstance(right, Node)
        self.left = left
        self.right = right
        Pack.__init__(self, [left, right])

    def __eq__(self, other):
        if isinstance(other, Pair):
            return self.left == other.left and \
                   self.right == other.right
