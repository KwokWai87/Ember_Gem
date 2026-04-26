#include "PUSE_CAPTURE.h"

u32 H_PUSE1=0,H_PUSE2;    				
u8 up_down=0;
//定时器1通道1输入捕获配置
//arr：自动重装值(TIM5是32位的!!)
//psc：时钟预分频数
void TIM5_CH1_3_Cap_Init(u32 arr,u16 psc)
{		 
	RCC->APB1LENR|=1<<3;   	//TIM5 时钟使能 
	RCC->AHB4ENR|=1<<7;   	//使能PORTH时钟	
	GPIO_Set(GPIOH,PIN10|PIN11|PIN12,GPIO_MODE_AF,GPIO_OTYPE_PP,GPIO_SPEED_HIGH,GPIO_PUPD_PD);//复用功能,下拉
	
	GPIO_AF_Set(GPIOH,10,2);	//PA8,AF2
  GPIO_AF_Set(GPIOH,11,2);	//PA8,AF2
	GPIO_AF_Set(GPIOH,12,2);	//PA8,AF2
	
 	TIM5->ARR=(u32)arr;  		//设定计数器自动重装值   
	TIM5->PSC=psc;  		    //预分频器 

	TIM5->CCMR1|=1<<0;		//CC1S=01 	选择输入端 IC1映射到TI1上
 	TIM5->CCMR1|=0<<4; 		//IC1F=0000 配置输入滤波器 不滤波
 	TIM5->CCMR1|=0<<10; 	//IC1PS=00 	配置输入分频,不分频 


	TIM5->CCER|=0<<1; 		//CC1P=0	上升沿捕获
	TIM5->CCER|=1<<0; 		//CC1E=0 	允许捕获计数器的值到捕获寄存器中
	
	TIM5->EGR=1<<0;			//软件控制产生更新事件,使写入PSC的值立即生效,否则将会要等到定时器溢出才会生效!
	TIM5->DIER|=1<<1;   	//允许捕获1中断				
	TIM5->DIER|=1<<0;   	//允许更新中断	
	TIM5->CR1|=0x01;    	//使能定时器1
	TIM5->BDTR|=1<<15;
	MY_NVIC_Init(2,1,TIM5_IRQn,2);//抢占2，子优先级1，组2	   
}



//定时器5中断服务程序	 
void TIM5_IRQHandler(void)
{ 		    
	u16 tsr;
	tsr=TIM1->SR;

		if(tsr&0x01)//溢出
		{	     
			TIM1->CR1&=~(1<<0)		;   //使能定时器1
			TIM1->CNT=0;					    //计数器清空
			TIM1->CCER&=~(1<<1);			//CC1P=0 设置为上升沿捕获
			TIM1->CR1|=0x01;    			//使能定时器1 
		}
		if(tsr&0x02)//捕获1发生捕获事件 STOP
		{
			  H_PUSE2=TIM8->CCR1;	      //获取当前的捕获值
				TIM1->CR1&=~(1<<0);    	  //使能定时器8
	 			TIM1->CNT=0;					    //计数器清空
				TIM1->CR1|=0x01;    			//使能定时器8	    
		}	
		if(tsr&0x04)//捕获2发生捕获事件  START
		{	
			  TIM1->CR1&=~(1<<0);    	  //使能定时器8
	 			TIM1->CNT=0;					    //计数器清空
				TIM1->CR1|=0x01;    			//使能定时器8	    
		}
		if(tsr&0x08)//捕获3发生捕获事件
		{	
			if(up_down==0)		//捕获到一个上升沿	
			{	  			
				TIM1->CR1&=~(1<<0)		;    	//使能定时器1
	 			TIM1->CNT=0;					    //计数器清空
	 			TIM1->CCER|=1<<1; 				//CC1P=1 设置为下降沿捕获
				TIM1->CR1|=0x01;    			//使能定时器1
				up_down=1;
			}
			else  								//还未开始,第一次捕获上升沿
			{
				H_PUSE1=TIM1->CCR1;
				TIM1->CR1&=~(1<<0)		;   //使能定时器1
	 			TIM1->CNT=0;					    //计数器清空
			  TIM1->CCER&=~(1<<1);			//CC1P=0 设置为上升沿捕获
				TIM1->CR1|=0x01;    			//使能定时器1
				up_down=0;
			}		    
		}		
	TIM1->SR=0;//清除中断标志位   
}


void Read_Puse(u8 mode)
{
	float temp=0;
	if(mode) temp=(float)H_PUSE1/10000.0f;
	else  temp=(float)H_PUSE2/10000.0f;
	
	printf("H_PUSE:%0.6fms\r\n",temp);
}
