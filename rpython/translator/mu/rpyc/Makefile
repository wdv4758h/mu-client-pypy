#################################
# Compile some of the RPython C backend implementations into a shared library.

.PHONY: all clean

all: librpyc.so

RPYC_DIR = ../../c
RPYC_SRC_DIR = $(RPYC_DIR)/src
CC = cc
OBJS = dtoa.o utils.o errno.o

dtoa.o: $(RPYC_SRC_DIR)/dtoa.c $(RPYC_SRC_DIR)/dtoa.h
	$(CC) -fPIC -c -DIEEE_8087 -I $(RPYC_DIR) -I . -o $@ $<

utils.o: src/utils.c
	$(CC) -fPIC -c -o $@ $<

errno.o: src/errno.c
	$(CC) -fPIC -c -o $@ $<

librpyc.so: $(OBJS)
	$(CC) -shared -o $@ $(OBJS)
	rm $(OBJS)
	
clean:
	rm librpyc.so


# vim: ts=8 sw=8 sts=0 noet ai
