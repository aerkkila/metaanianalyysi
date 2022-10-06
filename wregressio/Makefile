cflags = `pkg-config --libs nctietue2 gsl` -lm -g3 -gdwarf-2 -Wall

wregressio.out: wregressio.c
	gcc ${@:.out=.c} -o $@ ${cflags} -O3

wregressio_debug.out: wregressio.c
	gcc ${@:_debug.out=.c} -o $@ ${cflags}
