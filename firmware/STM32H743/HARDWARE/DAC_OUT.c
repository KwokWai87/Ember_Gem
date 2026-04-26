#include "DAC_OUT.h"


//DAC通道1输出初始化
void DAC_Init(void)
{   	 	
	RCC->APB1LENR|=1<<29;	//使能DAC时钟	   
	RCC->AHB4ENR|=1<<0;  	//使能PORTA时钟	  
	GPIO_Set(GPIOA,PIN4|PIN5,GPIO_MODE_AIN,0,0,GPIO_PUPD_PU);//PA4,模拟输入,下拉   
	
	DAC1->CCR=0;
	DAC1->MCR&=~(7<<0);		//MODE1[2:0]清零
	DAC1->MCR|=0;			//MODE1[2:0]=0,DAC通道1连接到外部引脚,并使能BUFFER

	DAC1->MCR&=~(7<<16);		//MODE2[2:0]清零
	DAC1->MCR|=0<<16;			//MODE2[2:0]=0,DAC通道1连接到外部引脚,并使能BUFFER
	
	DAC1->CR=0;				//DR寄存器清零
	DAC1->CR|=0<<1;			//TEN1=0,不使用触发功能 
	DAC1->CR|=0<<2;			//TSEL1[3:0]=0,软件触发
	DAC1->CR|=0<<6;			//WAVE1[1:0]=0,不使用波形发生
 	DAC1->CR|=0<<12;		//DMAEN1=0,DAC1 DMA不使能    
	DAC1->CR|=0<<14;		//CEN1=0,DAC1工作在普通模式 

  DAC1->CR|=0<<17;			//TEN2=0,不使用触发功能 
	DAC1->CR|=0<<18;			//TSEL2[3:0]=0,软件触发
	DAC1->CR|=0<<22;			//WAVE2[1:0]=0,不使用波形发生
 	DAC1->CR|=0<<28;		//DMAEN2=0,DAC1 DMA不使能    
	DAC1->CR|=0<<30;		//CEN2=0,DAC1工作在普通模式 
	
	DAC1->CR|=1<<0;			//使能DAC1 ch1
	
	DAC1->CR|=1<<16;			//使能DAC1 ch2
	
	DAC1->DHR12RD=0;
	DAC1->DHR12RD=0<<16;
	
}
//设置通道输出电压
void Dac1_Set_Vol(u8 L_R,u32 vol)
{
	u32 temp=0;
	temp=(u32)(4095.0f/(2500.0f/(float)vol));
	if(L_R)
	{
		DAC1->DHR12RD&=0xFFFF0000;
		DAC1->DHR12RD|=temp;
	}
	else
  {
		DAC1->DHR12RD&=0x0000FFFF;
		DAC1->DHR12RD|=temp<<16;
	}
	printf("L_R:%d vol:%d\r\n",L_R,vol);
	
}
