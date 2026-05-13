#include "24AA025E48T.h"

u8 EEPROM_BUFFER[5]={0x00,0x01,0x02,0x03,0x04};
void EEPROM_Init(void)
{
	u8 temp[5];
	MAC_ADDRESS_READ();
	U24AA025_READ(0,temp,5);
	sys_print("0x%0.2X 0x%0.2X 0x%0.2X 0x%0.2X 0x%0.2X\r\n",temp[0],temp[1],temp[2],temp[3],temp[4]);
	if(temp[0]!=0x00)U24AA025_WRITE(0,EEPROM_BUFFER,5);
}


void U24AA025_READ(u32 addr,u8 *pbuffer,u32 len)
{
  IIC1_Read_Nbytes(U24AA025_ADDRESS,addr,pbuffer,len,0);  
}


void U24AA025_WRITE(u32 addr,u8 *pbuffer,u32 len)
{
  u16 page_remain=16-(addr-((addr/16)*16))%16;
	u16 write_remain=(len-page_remain)%16;
	u16 write_pages=(len-page_remain)/16;
	u16 i=0;
	 
	if(len>page_remain)
	{
		//开始不满足一页的
		if(page_remain)
		{
		IIC1_Write_Nbytes(U24AA025_ADDRESS,addr,pbuffer,page_remain,0);
    pbuffer=pbuffer+page_remain;
		addr=addr+page_remain;	
		}
		//中间整页写入
		for(i=0;i<write_pages;i++)
		{
			IIC1_Write_Nbytes(U24AA025_ADDRESS,addr,pbuffer,16,0);
			addr+=16;
			pbuffer+=16;
		}
		//结尾不满足一页的
		if(write_remain)IIC1_Write_Nbytes(U24AA025_ADDRESS,addr,pbuffer,write_remain,0);
	}
  else IIC1_Write_Nbytes(U24AA025_ADDRESS,addr,pbuffer,len,0);  
}

void MAC_ADDRESS_READ(void)
{
	u8 pbuffer[6];
  U24AA025_READ(MAC_ADDRESS,pbuffer,6); 
	sys_print("EEPROM_ID:%0.2X:%0.2X:%0.2X:%0.2X:%0.2X:%0.2X\r\n",pbuffer[0],pbuffer[1],pbuffer[2],pbuffer[3],pbuffer[4],pbuffer[5]);
}
