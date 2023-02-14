cflags = `pkg-config --libs nctietue2 gsl` -lm -g3 -gdwarf-2 -Wall

all: wregressio.out virhepalkit*.so ../wregr_rajat.tex

wregressio.out: wregressio.c
	gcc ${@:.out=.c} -o $@ ${cflags} -O3

wregressio_debug.out: wregressio.c
	gcc ${@:_debug.out=.c} -o $@ ${cflags}

virhepalkit*.so: virhepalkit.pyx
	./setup.py build_ext --inplace

../wregr_rajat.tex: taulukko_rajat.c
	gcc taulukko_rajat.c -O2
	./a.out
