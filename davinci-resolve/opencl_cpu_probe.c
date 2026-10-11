#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
typedef void * H;
extern int clGetPlatformIDs(unsigned,H*,unsigned*);
extern int clGetDeviceIDs(H,uint64_t,unsigned,H*,unsigned*);
extern int clGetDeviceInfo(H,unsigned,size_t,void*,size_t*);
extern H clCreateContext(const intptr_t*,unsigned,const H*,void*,void*,int*);
extern H clCreateCommandQueue(H,H,uint64_t,int*);
extern H clCreateBuffer(H,uint64_t,size_t,void*,int*);
extern H clCreateProgramWithSource(H,unsigned,const char**,const size_t*,int*);
extern int clBuildProgram(H,unsigned,const H*,const char*,void*,void*);
extern int clGetProgramBuildInfo(H,H,unsigned,size_t,void*,size_t*);
extern H clCreateKernel(H,const char*,int*);
extern int clSetKernelArg(H,unsigned,size_t,const void*);
extern int clEnqueueNDRangeKernel(H,H,unsigned,const size_t*,const size_t*,const size_t*,unsigned,const H*,H*);
extern int clEnqueueReadBuffer(H,H,unsigned,size_t,size_t,void*,unsigned,const H*,H*);
#define OK(call) do { int err=(call); if(err){fprintf(stderr,"%s: %d\n",#call,err);return 2;} }while(0)
int main(void){
 H platform,device;unsigned count=0;int err;uint64_t type=0;char name[256]={0};
 OK(clGetPlatformIDs(1,&platform,&count));
 OK(clGetDeviceIDs(platform,2,1,&device,&count));
 OK(clGetDeviceInfo(device,0x1000,sizeof(type),&type,NULL));
 OK(clGetDeviceInfo(device,0x102b,sizeof(name),name,NULL));
 H context=clCreateContext(NULL,1,&device,NULL,NULL,&err);OK(err);
 H queue=clCreateCommandQueue(context,device,0,&err);OK(err);
 float input[]={1,2,3,4},output[4]={0};
 H buffer=clCreateBuffer(context,1|32,sizeof(input),input,&err);OK(err);
 const char *source="__kernel void demo(__global float *v){int i=get_global_id(0);v[i]=v[i]*2.0f+1.0f;}";
 H program=clCreateProgramWithSource(context,1,&source,NULL,&err);OK(err);
 err=clBuildProgram(program,1,&device,"",NULL,NULL);
 if(err){char log[4096]={0};clGetProgramBuildInfo(program,device,0x1183,sizeof(log),log,NULL);fprintf(stderr,"Build %d: %s\n",err,log);return 2;}
 H kernel=clCreateKernel(program,"demo",&err);OK(err);
 OK(clSetKernelArg(kernel,0,sizeof(buffer),&buffer));size_t n=4;
 OK(clEnqueueNDRangeKernel(queue,kernel,1,NULL,&n,NULL,0,NULL,NULL));
 OK(clEnqueueReadBuffer(queue,buffer,1,0,sizeof(output),output,0,NULL,NULL));
 for(int i=0;i<4;i++)if(fabsf(output[i]-(input[i]*2+1))>0.0001)return 3;
 printf("{\"state\":\"testado\",\"device\":\"%s\",\"deviceType\":%llu,\"physicalGpu\":false,\"cpuKernelPassed\":true,\"output\":[3,5,7,9],\"resolveStartedProven\":false}\n",name,(unsigned long long)type);
 return 0;
}
