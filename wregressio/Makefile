all: wregressio.out virhepalkit*.so ../wregr_rajat.tex

wregressio.out: wregressio.c
	gcc -Wall -o $@ $< `pkg-config --libs gsl` -lnctietue3 -g -O3

virhepalkit*.so: virhepalkit.pyx
	./setup.py build_ext --inplace

../wregr_rajat.tex: taulukko_rajat.c
	gcc taulukko_rajat.c -O2
	./a.out
