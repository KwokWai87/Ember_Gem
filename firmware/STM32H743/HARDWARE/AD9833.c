#include "AD9833.h"



void AD9833_Init(void)
{
AD9833_CS(0);
SPI4_ReadWriteByte(0x00C0);
AD9833_CS(1);
}

void AD9833_SelectWave(u8 select)
{
AD9833_CS(0);
switch(select)
{
	case 0:SPI4_ReadWriteByte(0x2028);  /*频率寄存器输出方波*/
		     break;
	case 1:SPI4_ReadWriteByte(0x2002);  /*频率寄存器输出三角波*/
		     break;
	case 2:SPI4_ReadWriteByte(0x2000);  /*频率寄存器输出正弦波*/
		     break;
	case 3:SPI4_ReadWriteByte(0x00C0);  /*无输出*/
		     break;
}
AD9833_CS(1);
}


void AD9833_SetFreq(u32 _freq)
{
	u32 freq;
	u16 lsb_14bit;
	u16 msb_14bit;
	u8 freq_number = 0;
	freq = (uint32_t)(268435456.0 / AD9833_SYSTEM_CLOCK * _freq);
	lsb_14bit = (u16)freq;
	msb_14bit = (u16)(freq >> 14);
	if(freq_number == FREQ_0)
	{
		lsb_14bit &= ~(1U<<15);//0111 1111 1111 1111 先把第15位清0,其他位不变
		lsb_14bit |= 1<<14;    //0100 0000 0000 0000 再把第14位置1,其他位不变 结果就是01xx xxxx xxxx xxxx
		msb_14bit &= ~(1U<<15); //同上
		msb_14bit |= 1<<14;
	}
	else
	{
		lsb_14bit &= ~(1<<14); //1011 1111 1111 1111 先把第14位清0,其他位不变
		lsb_14bit |= 1U<<15;   //1000 0000 0000 0000 再把第15位置1,其他位不变 结果就是10xx xxxx xxxx xxxx
		msb_14bit &= ~(1<<14); //同上
		msb_14bit |= 1U<<15;
	}
  AD9833_CS(0);
	SPI4_ReadWriteByte(lsb_14bit);
	SPI4_ReadWriteByte(msb_14bit);
  AD9833_CS(1);
}
