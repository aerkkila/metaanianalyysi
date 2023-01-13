all: mannk.so
	@python -c 'import mannk'

mannk.c: mannk.pyx lue.c
	cython3 -3 $<

mannk.so: mannk.c
	gcc -fpic -shared -I/usr/include/python3.10 -o $@ $<
