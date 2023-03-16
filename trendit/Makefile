all: mannk.so
	python -c import\ mannk

mannk.out.c: mannk.pyx lue.c tulosta.c
	cython3 -o mannk.out.c -3 $<

mannk.so: mannk.out.c
	gcc -Wno-format-security -fpic -shared -I/usr/include/python3.10 -o $@ $< -g

# en jaksa automatisoida näitä,
# mutta tarvittaessa ajetaan esim make -C .. vvt.target argv=antro
