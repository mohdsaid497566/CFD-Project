FC = nvfortran
FFLAGS = -O2 -Wall
GMSH_FLAGS = -I/usr/local/include -L/usr/local/lib -lgmsh
PROG = gmsh_process

$(PROG): gmsh_process.o
	$(FC) $(FFLAGS) -o $@ $^ $(GMSH_FLAGS)

gmsh_process.o: gmsh_process.f90
	$(FC) $(FFLAGS) -c $< $(GMSH_FLAGS)

clean:
	rm -f *.o *.mod $(PROG)
