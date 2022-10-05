kausi = 1
cflags = `pkg-config --libs nctietue2 gsl` -lm -g3 -gdwarf-2 -Wall -Dkausi=${kausi}

all: wregressio.out wregressio1.out

wregressio.out: wregressio.c
	gcc ${@:.out=.c} -o $@ ${cflags} -O3

wregressio1.out: wregressio.c
	gcc ${@:1.out=.c} -o $@ ${cflags} -DIKIROUTA -O3

wregressio_debug.out:
	gcc ${@:_debug.out=.c} -o $@ ${cflags}
