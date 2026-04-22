#include "DG4052EEQ.h"



void DG4052EEQ_Init(void)
{

	RCC->AHB4ENR|=1<<9;	//使能PORTJ时钟
	
	GPIO_Set(GPIOJ,PIN2|PIN3,GPIO_MODE_OUT,GPIO_OTYPE_PP,GPIO_SPEED_MID,GPIO_PUPD_PU);   //PB2设置
  IO_SW5_A(1);
	IO_SW5_B(1);

}




void DG4052EEQ_Set(u8 set_res)
{
 switch (set_res)
 {
	 case 0:  
		      IO_SW5_A(0);
	        IO_SW5_B(0);
	        printf("750KΩ select\r\n");
		      break;
 	 case 1:  
		      IO_SW5_A(1);
	        IO_SW5_B(0);
	        printf("24KΩ select\r\n");
		      break;
 	 case 2:  
		      IO_SW5_A(0);
	        IO_SW5_B(1);
	        printf("2.49KΩ select\r\n");
		      break;
 	 case 3:  
		      IO_SW5_A(1);
	        IO_SW5_B(1);
	        printf("243Ω select\r\n");
		      break;
 }
 printf("IO_SW5_A:%d\r\n",set_res&0x01);
 printf("IO_SW5_B:%d\r\n",(set_res&0x02)>>1);

}
