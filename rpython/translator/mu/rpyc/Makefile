#################################
# Compile some of the RPython C backend implementations into a shared library.

.PHONY: all clean

all: librpyc.so

RPYC_DIR = ../../c
RPYC_SRC_DIR = $(RPYC_DIR)/src

OBJS = dtoa.o

dtoa.o: $(RPYC_SRC_DIR)/dtoa.c $(RPYC_SRC_DIR)/dtoa.h
	cc -fPIC -c -DIEEE_8087 -I $(RPYC_DIR) -I . -o $@ $<

librpyc.so: $(OBJS)
	cc -shared -o $@ $<
	rm $(OBJS)
	
clean:
	rm librpyc.so


# vim: ts=8 sw=8 sts=0 noet ai
