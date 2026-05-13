#include "PGA849.h"

//F12:IO_PGA_SET_A0
//F11:IO_PGA_SET_A1
//F13:IO_PGA_SET_A2
//PJ0:IO_SW7_A0
//PJ1:IO_SW7_A1
void PGA849_init(void)
{
  RCC->AHB4ENR|=1<<1;	//使能PORTB时钟
	RCC->AHB4ENR|=1<<4;	//使能PORTE时钟
	RCC->AHB4ENR|=1<<9;	//使能PORTJ时钟
	
	GPIO_Set(GPIOB,PIN2,GPIO_MODE_OUT,GPIO_OTYPE_PP,GPIO_SPEED_MID,GPIO_PUPD_PU);   //PB2设置
	GPIO_Set(GPIOF,PIN11|PIN12|PIN13,GPIO_MODE_OUT,GPIO_OTYPE_PP,GPIO_SPEED_MID,GPIO_PUPD_PD);   //PE11/12/13设置
	GPIO_Set(GPIOJ,PIN0|PIN1,GPIO_MODE_OUT,GPIO_OTYPE_PP,GPIO_SPEED_MID,GPIO_PUPD_PD);   //PJ0/1设置
  IO_PGA_SET_A0(0);
	IO_PGA_SET_A1(0);
  IO_PGA_SET_A2(0);
	IO_SW7_A0(0);
	IO_SW7_A1(0);
	
}

//vref0or1_25=1:1.25v
//vref0or1_25=0:0.0v
void PGA849_set(u8 vref0or1_25,u8 gain,u8 ADG1409_A0_A1)
{
	
	switch(ADG1409_A0_A1)
	{
		case 0:IO_SW7_A0(0);
		       IO_SW7_A1(0);
			     break;
		case 1:IO_SW7_A0(1);
		       IO_SW7_A1(0);
			     break;		
		case 2:IO_SW7_A0(0);
		       IO_SW7_A1(1);
			     break;	
		case 3:IO_SW7_A0(1);
		       IO_SW7_A1(1);
			     break;	
	}
sys_print("IO_SW7_A0:%d\r\n",(ADG1409_A0_A1&0x01));
sys_print("IO_SW7_A1:%d\r\n",((ADG1409_A0_A1&0x02)>>1));


if(vref0or1_25)
{
	IO_SW6_IN(1);
	sys_print("IO_SW6_IN:1,vref=1.25v\r\n");
}
else
{
	IO_SW6_IN(0);
	sys_print("IO_SW6_IN:0,vref=0.0v\r\n");
}
	
	switch(gain)
{
	case 0:IO_PGA_SET_A0(0);
	       IO_PGA_SET_A1(0);
         IO_PGA_SET_A2(0);
		     break;
	case 1:IO_PGA_SET_A0(1);
	       IO_PGA_SET_A1(0);
         IO_PGA_SET_A2(0);
		     break;
	case 2:IO_PGA_SET_A0(0);
	       IO_PGA_SET_A1(1);
         IO_PGA_SET_A2(0);
		     break;
	case 3:IO_PGA_SET_A0(1);
	       IO_PGA_SET_A1(1);
         IO_PGA_SET_A2(0);
		     break;
	case 4:IO_PGA_SET_A0(0);
	       IO_PGA_SET_A1(0);
         IO_PGA_SET_A2(1);
		     break;
	case 5:IO_PGA_SET_A0(1);
	       IO_PGA_SET_A1(0);
         IO_PGA_SET_A2(1);
		     break;	
	case 6:IO_PGA_SET_A0(0);
	       IO_PGA_SET_A1(1);
         IO_PGA_SET_A2(1);
		     break;
	case 7:IO_PGA_SET_A0(1);
	       IO_PGA_SET_A1(1);
         IO_PGA_SET_A2(1);
		     break;
}
sys_print("IO_PGA_SET_A0:%d\r\n",(gain&0x01));
sys_print("IO_PGA_SET_A1:%d\r\n",((gain&0x02)>>1));
sys_print("IO_PGA_SET_A2:%d\r\n",((gain&0x04)>>2));
}
