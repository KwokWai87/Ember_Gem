#include "ADS1219.h"


//G0:IO_ADC_RST
//G1:IO_ADC_DRDY
u8  ADS1219_ID=0, CFG=0;;
void ADS1219_init(u8 mux,u8 gain,u8 dr,u8 cm,u8 vref)
{
	
	
	RCC->AHB4ENR|=1<<6;    //使能PORTG时钟	   	  
	GPIO_Set(GPIOG,PIN0,GPIO_MODE_OUT,GPIO_OTYPE_PP,GPIO_SPEED_LOW,GPIO_PUPD_PU);//PG0设置 
	GPIO_Set(GPIOG,PIN1,GPIO_MODE_IN,GPIO_OTYPE_OD,GPIO_SPEED_LOW,GPIO_PUPD_PU);//PG1设置
	IO_ADC_RST(1);
	//check ID
	ADS1219_ID=(IIC4_ReadOneByte(ADS1219_ADDRESS,ADS1219_CMD_RREG|(0x01<<3),0)&0x7F);
  printf("ADS1219_ID:0x%0.2X\r\n",ADS1219_ID);
	//ADS1219_MUX0 ///AINP = AIN0, AINN = AIN1 (default)

	switch(mux)
	{
		case 0:printf("MUX0:AINP = AIN0, AINN = AIN1 (default)\r\n");
		       break;
		case 1:printf("MUX1:AINP = AIN2, AINN = AIN3\r\n");
		       break;
		case 2:printf("MUX2:AINP = AIN1, AINN = AIN2\r\n");
		       break;
		case 3:printf("MUX3:AINP = AIN0, AINN = AGND\r\n");
		       break;
		case 4:printf("MUX4:AINP = AIN1, AINN = AGND\r\n");
		       break;
		case 5:printf("MUX5:AINP = AIN2, AINN = AGND\r\n");
		       break;
		case 6:printf("MUX6:AINP = AIN3, AINN = AGND\r\n");
		       break;
		case 7:printf("MUX7:AINP and AINN shorted to AVDD/2\r\n");
		       break;
		default:mux=0;
		       printf("mux err! should be 0~7,set to 0 now!\r\n");
           break;	
	}
	switch(gain)
	{
		case 0:printf("GAINx1:Gain = 1 (default)\r\n"); 
		       break;
		case 1:printf("GAINx4:Gain = 4 \r\n"); 
		       break;	
		default:gain=0;
			     printf("gain err! should be 0~1,set to 0 now!\r\n");
           break;	
	}
		switch(dr)
	{
		case 0:printf("DR0:20 SPS (default)\r\n"); 
		       break;
		case 1:printf("DR1:90 SPS\r\n"); 
		       break;	
		case 2:printf("DR2:330 SPS\r\n"); 
		       break;	
		case 3:printf("DR3:1000 SPS\r\n"); 
		       break;	
		default:dr=0;
			     printf("dr err! should be 0~3,set to 0 now!\r\n");
           break;	
	}
		switch(cm)
	{
		case 0:printf("CM0:Single-shot conversion mode (default)\r\n"); 
		       break;
		case 1:printf("CM1:Continuous conversion mode\r\n"); 
		       break;		
		default:cm=0;
			     printf("cm err! should be 0~1,set to 0 now!\r\n");
           break;	
	}	
  	switch(vref)
	{
		case 0:printf("VREF0:Internal 2.048-V reference selected (default)\r\n"); 
		       break;
		case 1:printf("VREF1:External reference selected using the REFP and REFN inputs\r\n"); 
		       break;		
		default:vref=0;
			     printf("vref err! should be 0~1,set to 0 now!\r\n");
           break;	
	}
	CFG=(mux<<ADS1219_MUX_BIT)|(gain<<ADS1219_GAIN_BIT)|(dr<<ADS1219_DR_BIT)|(cm<<ADS1219_CM_BIT)|(vref<<ADS1219_VREF_BIT);
	IIC4_WriteOneByte(ADS1219_ADDRESS,ADS1219_CMD_WREGE,CFG,0);
	IIC4_Write_direct_byte(ADS1219_ADDRESS,ADS1219_CMD_START);
}


void ADS1219_Read_vol(void)
{
u8 temp8[3];
int temp32=0;
float vol=0.0f,vref=0.0f;

if((CFG&0x01)==1) vref=2.5f;
else  vref=2.048f;
	
if((CFG&0x02)==0)IIC4_Write_direct_byte(ADS1219_ADDRESS,ADS1219_CMD_START);
delay_ms(10);
while(IO_ADC_DRDY){};
IIC4_Read_Nbytes(ADS1219_ADDRESS,ADS1219_CMD_RDATA,temp8,3,0);
temp32=(int)((temp8[0]<<24)|(temp8[1]<<16)|(temp8[2]<<8));
temp32=temp32>>8;
vol=vref*((float)temp32/8388608.0f);
printf("ADS1219_Read:%0.4fV  RAW:%02X %02X %02X\r\n",vol,temp8[0],temp8[1],temp8[2]);
}
