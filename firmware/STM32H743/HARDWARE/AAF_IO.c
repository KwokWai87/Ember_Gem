#include "AAF_IO.h"


//PB12  IO_SW3_A0
//PB13  IO_SW3_A1
//PB14  IO_SW3_A2

//PD8   IO_SW4_A0
//PD9   IO_SW4_A1
//PD10  IO_SW4_A2

void AAF_IO_Init(void)
{
  	RCC->AHB4ENR|=1<<1;         //使能PORTB时钟 
	  RCC->AHB4ENR|=1<<3;    			//使能PORTD时钟 
		GPIO_Set(GPIOB,PIN12|PIN13|PIN14,GPIO_MODE_OUT,GPIO_OTYPE_PP,GPIO_SPEED_HIGH,GPIO_PUPD_PU);
		GPIO_Set(GPIOD,PIN8|PIN9|PIN10,GPIO_MODE_OUT,GPIO_OTYPE_PP,GPIO_SPEED_HIGH,GPIO_PUPD_PU);
	  IO_SW3_A0(0);
	  IO_SW3_A1(0);
	  IO_SW3_A2(0);	

	  IO_SW4_A0(0);
	  IO_SW4_A1(0);
	  IO_SW4_A2(0);		
}



void AAF_set_IO(u8 IO_SW3_A0,u8 IO_SW3_A1,u8 IO_SW3_A2,u8 IO_SW4_A0,u8 IO_SW4_A1,u8 IO_SW4_A2)
{
	  IO_SW3_A0(IO_SW3_A0);
	  IO_SW3_A1(IO_SW3_A1);
	  IO_SW3_A2(IO_SW3_A2);	

	  IO_SW4_A0(IO_SW4_A0);
	  IO_SW4_A1(IO_SW4_A1);
	  IO_SW4_A2(IO_SW4_A2);	

		sys_print("IO_SW3_A0:%d\r\n",IO_SW3_A0);
		sys_print("IO_SW3_A1:%d\r\n",IO_SW3_A1);
		sys_print("IO_SW3_A2:%d\r\n",IO_SW3_A2);
		sys_print("IO_SW4_A0:%d\r\n",IO_SW4_A0);
		sys_print("IO_SW4_A1:%d\r\n",IO_SW4_A1);
		sys_print("IO_SW4_A2:%d\r\n",IO_SW4_A2);
}
