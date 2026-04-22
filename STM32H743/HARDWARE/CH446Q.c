#include "CH446Q.h"

	//D7 :IO_SWA_CS1
	//C8 :IO_SWA_CS2
	//G6 :IO_SWA_CS3
	//G12:IO_SWA_CS4
	
	//E6:IO_SWA_RST
	//D5:IO_SWA_STB
	
  //PD14:IO_SWA_AX1
  //PD15:IO_SWA_AX2
  //PD0 :IO_SWA_AX3
  //PD1 :IO_SWA_AX4	
	//PE7 :IO_SWA_AY1
	//PE8 :IO_SWA_AY2	
  //PE9 :IO_SWA_AY3
	
	//PE10:IO_SWA_DAT
	
	
void CH446Q_init(void)
{
	RCC->AHB4ENR|=1<<2;	//使能PORTC时钟 
	RCC->AHB4ENR|=1<<3;	//使能PORTD时钟 
	RCC->AHB4ENR|=1<<4;	//使能PORTE时钟 
	RCC->AHB4ENR|=1<<6;	//使能PORTG时钟 
	
	GPIO_Set(GPIOC,PIN8,GPIO_MODE_OUT,GPIO_OTYPE_PP,GPIO_SPEED_MID,GPIO_PUPD_PU);  //PC8设置
	GPIO_Set(GPIOD,PIN0|PIN1|PIN5|PIN7|PIN14|PIN15,GPIO_MODE_OUT,GPIO_OTYPE_PP,GPIO_SPEED_MID,GPIO_PUPD_PU);  //PD0/1/5/7/14/15设置
	GPIO_Set(GPIOE,PIN6|PIN7|PIN8|PIN9|PIN10,GPIO_MODE_OUT,GPIO_OTYPE_PP,GPIO_SPEED_MID,GPIO_PUPD_PU);   //PE6/7/8/9/10设置
	GPIO_Set(GPIOG,PIN6|PIN12,GPIO_MODE_OUT,GPIO_OTYPE_PP,GPIO_SPEED_MID,GPIO_PUPD_PU); //PG6/12设置

  CH446Q_Reset();
}


void CH446Q_MIX_CONTROL(u8 cs,u8 ax,u8 ay,u8 on_off)
{

 switch(ax)
 {
   case 0:IO_SWA_AX1(0);
	        IO_SWA_AX2(0);
	        IO_SWA_AX3(0);
	        IO_SWA_AX4(0);
		      break;
   case 1:IO_SWA_AX1(1);
	        IO_SWA_AX2(0);
	        IO_SWA_AX3(0);
	        IO_SWA_AX4(0);
		      break;
   case 2:IO_SWA_AX1(0);
	        IO_SWA_AX2(1);
	        IO_SWA_AX3(0);
	        IO_SWA_AX4(0);
		      break;
   case 3:IO_SWA_AX1(1);
	        IO_SWA_AX2(1);
	        IO_SWA_AX3(0);
	        IO_SWA_AX4(0);
	        break;
   case 4:IO_SWA_AX1(0);
	        IO_SWA_AX2(0);
	        IO_SWA_AX3(1);
	        IO_SWA_AX4(0);
		      break;
   case 5:IO_SWA_AX1(1);
	        IO_SWA_AX2(0);
	        IO_SWA_AX3(1);
	        IO_SWA_AX4(0);
		      break;
   case 6:IO_SWA_AX1(0);
	        IO_SWA_AX2(1);
	        IO_SWA_AX3(1);
	        IO_SWA_AX4(0);
		      break;
   case 7:IO_SWA_AX1(1);
	        IO_SWA_AX2(1);
	        IO_SWA_AX3(1);
	        IO_SWA_AX4(0);
					break;
   case 8:IO_SWA_AX1(0);
	        IO_SWA_AX2(0);
	        IO_SWA_AX3(0);
	        IO_SWA_AX4(1);
		      break;
   case 9:IO_SWA_AX1(1);
	        IO_SWA_AX2(0);
	        IO_SWA_AX3(0);
	        IO_SWA_AX4(1);
		      break;
  case 10:IO_SWA_AX1(0);
	        IO_SWA_AX2(1);
	        IO_SWA_AX3(0);
	        IO_SWA_AX4(1);
		      break;
  case 11:IO_SWA_AX1(1);
	        IO_SWA_AX2(1);
	        IO_SWA_AX3(0);
	        IO_SWA_AX4(1);
		      break;	
  case 12:IO_SWA_AX1(0);
	        IO_SWA_AX2(0);
	        IO_SWA_AX3(1);
	        IO_SWA_AX4(1);
		      break;
  case 13:IO_SWA_AX1(1);
	        IO_SWA_AX2(0);
	        IO_SWA_AX3(1);
	        IO_SWA_AX4(1);
		      break;
  case 14:IO_SWA_AX1(0);
	        IO_SWA_AX2(1);
	        IO_SWA_AX3(1);
	        IO_SWA_AX4(1);
		      break;
  case 15:IO_SWA_AX1(1);
	        IO_SWA_AX2(1);
	        IO_SWA_AX3(1);
	        IO_SWA_AX4(1);
		      break;					
 } 
 printf("ax:%d\r\n",ax);
 printf("IO_SWA_AX1:%d\r\n",ax&0x01);
 printf("IO_SWA_AX2:%d\r\n",((ax&0x02)>>1));
 printf("IO_SWA_AX3:%d\r\n",((ax&0x04)>>2));
 printf("IO_SWA_AX4:%d\r\n",((ax&0x08)>>3));
  switch(ay)
 {
   case 0:IO_SWA_AY1(0);
	        IO_SWA_AY2(0);
	        IO_SWA_AY3(0);
		      break;
   case 1:IO_SWA_AY1(1);
	        IO_SWA_AY2(0);
	        IO_SWA_AY3(0);
		      break;
   case 2:IO_SWA_AY1(0);
	        IO_SWA_AY2(1);
	        IO_SWA_AY3(0);
		      break;
   case 3:IO_SWA_AY1(1);
	        IO_SWA_AY2(1);
	        IO_SWA_AY3(0);
		      break;	 
   case 4:IO_SWA_AY1(0);
	        IO_SWA_AY2(0);
	        IO_SWA_AY3(1);
		      break;	 	 
 }
 
 printf("ay:%d\r\n",ay);
 printf("IO_SWA_AY1:%d\r\n",ay&0x01);
 printf("IO_SWA_AY2:%d\r\n",((ay&0x02)>>1));
 printf("IO_SWA_AY3:%d\r\n",((ay&0x04)>>2));

 switch(cs)
 {
   case 0:IO_SWA_CS1(1);
	        IO_SWA_CS2(0);
	        IO_SWA_CS3(0);
	        IO_SWA_CS4(0);
		      break;
   case 1:IO_SWA_CS1(0);
	        IO_SWA_CS2(1);
	        IO_SWA_CS3(0);
	        IO_SWA_CS4(0);
		      break;
   case 2:IO_SWA_CS1(0);
	        IO_SWA_CS2(0);
	        IO_SWA_CS3(1);
	        IO_SWA_CS4(0);
		      break;
   case 3:IO_SWA_CS1(0);
	        IO_SWA_CS2(0);
	        IO_SWA_CS3(0);
	        IO_SWA_CS4(1);
		      break;	 
 }
 printf("cs:%d\r\n",cs+1);
 cs=1<<cs;
 printf("IO_SWA_CS1:%d\r\n",cs&0x01);
 printf("IO_SWA_CS2:%d\r\n",((cs&0x02)>>1));
 printf("IO_SWA_CS3:%d\r\n",((cs&0x04)>>2));
 printf("IO_SWA_CS4:%d\r\n",((cs&0x08)>>3));
 delay_ms(1);
 if(on_off) IO_SWA_DAT(1);
 else IO_SWA_DAT(0); 
 printf("IO_SWA_DAT:%d\r\n",on_off);
 IO_SWA_STB(1);
 printf("IO_SWA_STB:1\r\n");
 IO_SWA_STB(0);
 printf("IO_SWA_STB:0\r\n");
}

void CH446Q_Reset(void)
{
	IO_SWA_RST(1);
	printf("IO_SWA_RST:1\r\n");
	IO_SWA_CS1(0);
	IO_SWA_CS2(0);
	IO_SWA_CS3(0);
	IO_SWA_CS4(0);
	printf("IO_SWA_CS1:0\r\n");
	printf("IO_SWA_CS2:0\r\n");
	printf("IO_SWA_CS3:0\r\n");
	printf("IO_SWA_CS4:0\r\n");	
	
	IO_SWA_AX1(0);
	IO_SWA_AX2(0);
	IO_SWA_AX3(0);
	IO_SWA_AX4(0);

	printf("IO_SWA_AX1:0\r\n");
	printf("IO_SWA_AX2:0\r\n");
	printf("IO_SWA_AX3:0\r\n");
	printf("IO_SWA_AX4:0\r\n");	
	
  IO_SWA_AY1(0);
	IO_SWA_AY2(0);
	IO_SWA_AY3(0);

	printf("IO_SWA_AY1:0\r\n");
	printf("IO_SWA_AY2:0\r\n");
	printf("IO_SWA_AY3:0\r\n");

  IO_SWA_STB(0);
  printf("IO_SWA_STB:0\r\n");
	
	IO_SWA_RST(0);
  printf("IO_SWA_RST:0\r\n");
	

}
