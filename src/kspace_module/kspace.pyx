cimport cython

cdef extern from "ckspace.c":
    double px_c(double alpha, double theta, double phi)
    double dpxda_c(double alpha, double theta, double phi)
    double dpxdt_c(double alpha, double theta, double phi)
    double py_c(double alpha, double theta)
    double dpyda_c(double alpha, double theta)
    double dpydt_c(double alpha, double theta)
    double alpha_solver_c(double alpha0, double theta0, double phi, double px_, double py_)
    double theta_solver_c(double alpha0, double theta0, double phi, double px_, double py_)
    int solver_c(double *alpha0, double *theta0, double phi, double px_, double py_, double err, int maxstep) nogil

############ python functions #################

def px(double alpha, double theta, double phi):
    return px_c(alpha, theta, phi)

def dpxda(double alpha, double theta, double phi):
    return dpxda_c(alpha, theta, phi)

def dpxdt(double alpha, double theta, double phi):
    return dpxdt_c(alpha, theta, phi)

def py(double alpha, double theta):
    return py_c(alpha, theta)

def dpyda(double alpha, double theta):
    return dpyda_c(alpha, theta)

def dpydt(double alpha, double theta):
    return dpydt_c(alpha, theta)

def alpha_solver(double alpha0, double theta0, double phi, double px_, double py_):
    return alpha_solver_c(alpha0, theta0, phi, px_, py_)

def theta_solver(double alpha0, double theta0, double phi, double px_, double py_):
    return theta_solver_c(alpha0, theta0, phi, px_, py_)

@cython.boundscheck(False)
@cython.wraparound(False)
def solver(double[:] alphalist, double[:] thetalist, double phi, double[:] px_list, double[:] py_list, double err, int maxstep):
    cdef size_t i, I
    cdef int step = 0
    I = px_list.shape[0]
    with nogil:
        for i in range(I):
            step = solver_c(<double *> &alphalist[i], <double *> &thetalist[i], phi, px_list[i], py_list[i], err, maxstep)
