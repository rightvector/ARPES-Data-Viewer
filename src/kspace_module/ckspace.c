#include <stdio.h>
#include <math.h>
#include <time.h>

static double PI = (double)(3.1415926535897932384626433832795);

double px_c(double alpha, double theta, double phi)
{
    return sin(alpha)*cos(phi)+cos(alpha)*sin(phi)*cos(theta);
}

double dpxda_c(double alpha, double theta, double phi)
{
    return cos(alpha)*cos(phi)-sin(alpha)*sin(phi)*cos(theta);
}

double dpxdt_c(double alpha, double theta, double phi)
{
    return -cos(alpha)*sin(phi)*sin(theta);
}

double py_c(double alpha, double theta)
{
    return cos(alpha)*sin(theta);
}

double dpyda_c(double alpha, double theta)
{
    return -sin(alpha)*sin(theta);
}

double dpydt_c(double alpha, double theta)
{
    return cos(alpha)*cos(theta);
}

double alpha_solver_c(double alpha0, double theta0, double phi, double px_, double py_)
{
    return alpha0-(dpydt_c(alpha0, theta0)*(px_c(alpha0, theta0, phi)-px_)-dpxdt_c(alpha0, theta0, phi)*(py_c(alpha0, theta0)-py_))/(dpxda_c(alpha0, theta0, phi)*dpydt_c(alpha0, theta0)-dpxdt_c(alpha0, theta0, phi)*dpyda_c(alpha0, theta0));
}

double theta_solver_c(double alpha0, double theta0, double phi, double px_, double py_)
{
    return theta0-(dpyda_c(alpha0, theta0)*(px_c(alpha0, theta0, phi)-px_)-dpxda_c(alpha0, theta0, phi)*(py_c(alpha0, theta0)-py_))/(dpxdt_c(alpha0, theta0, phi)*dpyda_c(alpha0, theta0)-dpxda_c(alpha0, theta0, phi)*dpydt_c(alpha0, theta0));
}

int solver_c(double *alpha0, double *theta0, double phi, double px_, double py_, double err, int maxstep)
{
    double temp_alpha = 0, temp_theta = 0;
    int step = 0;
    while(fabs(px_c(*alpha0, *theta0, phi)-px_) >= err || fabs(py_c(*alpha0, *theta0)-py_) >= err)
    {
        temp_alpha = *alpha0;
        temp_theta = *theta0;
        *alpha0 = alpha_solver_c(temp_alpha, temp_theta, phi, px_, py_);
        *theta0 = theta_solver_c(temp_alpha, temp_theta, phi, px_, py_);
        step++;
        if(step > maxstep)
        {
            break;
        }
    }
    if(step > maxstep)
    {
        *alpha0 = PI;
        *theta0 = PI;
    }
    else
    {
        *alpha0 = fmod(*alpha0, 2*PI);
        *theta0 = fmod(*theta0, 2*PI);
        if(*alpha0 > PI)
            *alpha0 -= 2*PI;
        if(*theta0 > PI)
            *theta0 -= 2*PI;
    }
    //printf("%lf, %lf, %d\n", px_, py_, step);
    return step;
}

/*
int main()
{
    double PI = asin(1)*2;
    double phi_deg = 0.0, phi = 0.0;
    double px_ = 0.0;
    double py_ = 0.0;
    double alpha0 = 0.0;
    double theta0 = 0.0;
    double alpha_deg = 0.0, theta_deg = 0.0;
    printf("phi=?(degree)\n");
    scanf("%lf", &phi_deg);   // format for double should be "%lf"
    phi = phi_deg*PI/180;
    printf("alpha initial=?(degree)\n");
    scanf("%lf", &alpha_deg);
    printf("theta initial=?(degree)\n");
    scanf("%lf", &theta_deg);
    double alpha_init = alpha_deg*PI/180;
    double theta_init = theta_deg*PI/180;
    FILE *fp = NULL;
    fp = fopen("D:/result.txt", "w");
    int t0 = clock();
    int num = 20;
    int j,k, step=0;
    for(j=0;j<num;j++)
    {
        px_ = -0.75 + 0.01*j;
        for(k=0;k<num;k++)
        {
            py_ = -0.75 + 0.01*k;
            if(step > 30)
            {
                alpha0 = 0;
                theta0 = 0;
            }
            step = solver(&alpha0, &theta0, phi, px_, py_, 1e-6, 30);
            //fprintf(fp, "%lf %lf\n", alpha0*180/PI, theta0*180/PI);
            printf("alpha: %lf, theta: %lf\n", alpha0*180/PI, theta0*180/PI);
        }
    }
    int t1 = clock();
    printf("time: %d(ms)\n", t1-t0);
    fclose(fp);
    system("pause");
    return 0;
}*/