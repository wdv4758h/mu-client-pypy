#################################
# Compile some of the RPython C backend implementations into a shared library.

.PHONY: all clean

all: librpyc.so

RPYC_DIR = ../../c
RPYC_SRC_DIR = $(RPYC_DIR)/src
PYPY_MOD_DIR = ../../../../pypy/module
CC = cc
OBJS = dtoa.o utils.o errno.o tscmp.o linux_debug.o fakestack.o bitcastfloat.o
FLAGS = -D__MU__

dtoa.o: $(RPYC_SRC_DIR)/dtoa.c $(RPYC_SRC_DIR)/dtoa.h
	$(CC) -fPIC -c -DIEEE_8087 $(FLAGS) -I $(RPYC_DIR) -o $@ $<

utils.o: src/utils.c
	$(CC) -fPIC $(FLAGS) -c -o $@ $<

errno.o: src/errno.c
	$(CC) -fPIC $(FLAGS) -c -o $@ $<

tscmp.o: $(PYPY_MOD_DIR)/operator/tscmp.c $(PYPY_MOD_DIR)/operator/tscmp.h
	$(CC) -fPIC $(FLAGS) -c  -I $(RPYC_DIR) -o $@ $<

linux_debug.o: src/linux_debug.c
	$(CC) -fPIC $(FLAGS) -c -o $@ $<

fakestack.o: src/fakestack.c
	$(CC) -fPIC $(FLAGS) -c -o $@ $<

bitcastfloat.o: src/bitcastfloat.c
	$(CC) -fPIC $(FLAGS) -c -o $@ $<

librpyc.so: $(OBJS)
	$(CC) -shared -o $@ $(OBJS)
	rm $(OBJS)
	
clean:
	rm librpyc.so


# vim: ts=8 sw=8 sts=0 noet ai
