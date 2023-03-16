all: wregressio.out virhepalkit*.so

wregressio.out: wregressio.c
	gcc -Wall -o $@ $< `pkg-config --libs gsl` -lnctietue3 -g -O3

virhepalkit*.so: virhepalkit.pyx
	./setup.py build_ext --inplace
