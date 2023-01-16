all: mannk.so
	python -c import\ mannk
	python mannk.py

mannk.out.c: mannk.pyx lue.c
	cython3 -o mannk.out.c -3 $<

mannk.so: mannk.out.c
	gcc -fpic -shared -I/usr/include/python3.10 -o $@ $<
