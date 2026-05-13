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
  sys_print("ADS1219_ID:0x%0.2X\r\n",ADS1219_ID);
	//ADS1219_MUX0 ///AINP = AIN0, AINN = AIN1 (default)

	switch(mux)
	{
		case 0:sys_print("MUX0:AINP = AIN0, AINN = AIN1 (default)\r\n");
		       break;
		case 1:sys_print("MUX1:AINP = AIN2, AINN = AIN3\r\n");
		       break;
		case 2:sys_print("MUX2:AINP = AIN1, AINN = AIN2\r\n");
		       break;
		case 3:sys_print("MUX3:AINP = AIN0, AINN = AGND\r\n");
		       break;
		case 4:sys_print("MUX4:AINP = AIN1, AINN = AGND\r\n");
		       break;
		case 5:sys_print("MUX5:AINP = AIN2, AINN = AGND\r\n");
		       break;
		case 6:sys_print("MUX6:AINP = AIN3, AINN = AGND\r\n");
		       break;
		case 7:sys_print("MUX7:AINP and AINN shorted to AVDD/2\r\n");
		       break;
		default:mux=0;
		       sys_print("mux err! should be 0~7,set to 0 now!\r\n");
           break;	
	}
	switch(gain)
	{
		case 0:sys_print("GAINx1:Gain = 1 (default)\r\n"); 
		       break;
		case 1:sys_print("GAINx4:Gain = 4 \r\n"); 
		       break;	
		default:gain=0;
			     sys_print("gain err! should be 0~1,set to 0 now!\r\n");
           break;	
	}
		switch(dr)
	{
		case 0:sys_print("DR0:20 SPS (default)\r\n"); 
		       break;
		case 1:sys_print("DR1:90 SPS\r\n"); 
		       break;	
		case 2:sys_print("DR2:330 SPS\r\n"); 
		       break;	
		case 3:sys_print("DR3:1000 SPS\r\n"); 
		       break;	
		default:dr=0;
			     sys_print("dr err! should be 0~3,set to 0 now!\r\n");
           break;	
	}
		switch(cm)
	{
		case 0:sys_print("CM0:Single-shot conversion mode (default)\r\n"); 
		       break;
		case 1:sys_print("CM1:Continuous conversion mode\r\n"); 
		       break;		
		default:cm=0;
			     sys_print("cm err! should be 0~1,set to 0 now!\r\n");
           break;	
	}	
  	switch(vref)
	{
		case 0:sys_print("VREF0:Internal 2.048-V reference selected (default)\r\n"); 
		       break;
		case 1:sys_print("VREF1:External reference selected using the REFP and REFN inputs\r\n"); 
		       break;		
		default:vref=0;
			     sys_print("vref err! should be 0~1,set to 0 now!\r\n");
           break;	
	}
	CFG=(mux<<ADS1219_MUX_BIT)|(gain<<ADS1219_GAIN_BIT)|(dr<<ADS1219_DR_BIT)|(cm<<ADS1219_CM_BIT)|(vref<<ADS1219_VREF_BIT);
	IIC4_WriteOneByte(ADS1219_ADDRESS,ADS1219_CMD_WREGE,CFG,0);
	IIC4_Write_direct_byte(ADS1219_ADDRESS,ADS1219_CMD_START);
}


float ADS1219_Read_vol(void)
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
vol=vref*((float)temp32/8388.608f);
sys_print("ADS1219_Read:%0.6fmV  RAW:%02X %02X %02X\r\n",vol,temp8[0],temp8[1],temp8[2]);
return vol;	
}
