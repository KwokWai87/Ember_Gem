#include "S_IIC.h"


//B6:I2C1_SCL
//B7:I2C1_SDA
void IIC1_Init(void)
{
	RCC->AHB4ENR|=1<<1;    //使能PORTB时钟	   	  
	GPIO_Set(GPIOB,PIN6|PIN7,GPIO_MODE_OUT,GPIO_OTYPE_PP,GPIO_SPEED_HIGH,GPIO_PUPD_PU);//PB6/7设置 
	IIC1_SCL(1);
	IIC1_SDA(1);
}


//F14:I2C4_SCL
//F15:I2C4_SDA
void IIC4_Init(void)
{
	RCC->AHB4ENR|=1<<5;    //使能PORTF时钟	   	  
	GPIO_Set(GPIOF,PIN14|PIN15,GPIO_MODE_OUT,GPIO_OTYPE_PP,GPIO_SPEED_HIGH,GPIO_PUPD_PU);//PF14/PF15设置 
	IIC4_SCL(1);
	IIC4_SDA(1);
}


void IIC1_Start(void)
{
	IIC1_SCL(1);
	delay_us(2);
	IIC1_SDA(1);	 
	delay_us(2);
 	IIC1_SDA(0);//START:when CLK is high,DATA change form high to low 
	delay_us(2);
}	 

void IIC4_Start(void)
{
	IIC4_SCL(1);
	delay_us(2);
	IIC4_SDA(1);	 
	delay_us(2);
 	IIC4_SDA(0);//START:when CLK is high,DATA change form high to low 
	delay_us(2);
}	 

void IIC1_Stop(void)
{	
	delay_us(4);
	IIC1_SCL(0);
	delay_us(2);	
	IIC1_SDA(0);
	delay_us(2);	
	IIC1_SCL(1);
	delay_us(2);
	IIC1_SDA(1);//STOP:when CLK is high DATA change form low to high
}


void IIC4_Stop(void)
{	
	delay_us(4);
	IIC4_SCL(0);
	delay_us(2);	
	IIC4_SDA(0);
	delay_us(2);	
	IIC4_SCL(1);
	delay_us(2);
	IIC4_SDA(1);//STOP:when CLK is high DATA change form low to high
}

u8 IIC1_Wait_Ack(void)
{
	u16 ucErrTime=0;
	delay_us(2);
	SDA1_IN();      //SDA设置为输入  
	delay_us(2);	   
	IIC1_SCL(1);
	delay_us(2);	 
	while(READ_SDA1)
	{
		ucErrTime++;
		if(ucErrTime>250)
		{
			SDA1_OUT(); 
			IIC1_Stop();
			delay_ms(5); 
			return 1;
		}
	}
	delay_us(2);
	IIC1_SCL(0);//时钟输出0 	
	IIC1_SDA(0);
	SDA1_OUT();      //SDA设置为输出 
	return 0;  
} 

u8 IIC4_Wait_Ack(void)
{
	u16 ucErrTime=0;
	delay_us(2);
	SDA4_IN();      //SDA设置为输入  
	delay_us(2);	   
	IIC4_SCL(1);
	delay_us(2);	 
	while(READ_SDA4)
	{
		ucErrTime++;
		if(ucErrTime>250)
		{
			SDA4_OUT(); 
			IIC4_Stop();
			delay_ms(5); 
			return 1;
		}
	}
	delay_us(2);
	IIC4_SCL(0);//时钟输出0 	
	IIC4_SDA(0);
	SDA4_OUT();      //SDA设置为输出 
	return 0;  
}
void IIC1_Ack(void)
{ 
	IIC1_SCL(0);
	IIC1_SDA(0);
	delay_us(4);
	IIC1_SCL(1);
	delay_us(4);
	IIC1_SCL(0);
	delay_us(4);
}

void IIC4_Ack(void)
{ 
	IIC4_SCL(0);
	IIC4_SDA(0);
	delay_us(4);
	IIC4_SCL(1);
	delay_us(4);
	IIC4_SCL(0);
	delay_us(4);
}

void IIC1_NAck(void)
{
	delay_us(2);
	IIC1_SDA(1);
	delay_us(2);
	IIC1_SCL(1);
	delay_us(4);
	IIC1_SCL(0);
	delay_us(2);
	IIC1_SDA(0);
	delay_us(2);
	IIC1_SCL(1);
}	

void IIC4_NAck(void)
{
	delay_us(2);
	IIC4_SDA(1);
	delay_us(2);
	IIC4_SCL(1);
	delay_us(4);
	IIC4_SCL(0);
	delay_us(2);
	IIC4_SDA(0);
	delay_us(2);
	IIC4_SCL(1);
}	

void IIC1_Send_Byte(u8 txd)
{                        
    u8 t;
		IIC1_SCL(0);//拉低时钟开始数据传输	
    for(t=0;t<8;t++)
    {  
    delay_us(2);
		IIC1_SDA((txd&0x80)>>7);
		txd<<=1; 	  
		delay_us(2);   //对TEA5767这三个延时都是必须的
		IIC1_SCL(1);
		delay_us(4); 
   	IIC1_SCL(0);		
    }	
		IIC1_SDA(1);
}

void IIC4_Send_Byte(u8 txd)
{                        
    u8 t;
		IIC4_SCL(0);//拉低时钟开始数据传输	
    for(t=0;t<8;t++)
    {  
    delay_us(2);
		IIC4_SDA((txd&0x80)>>7);
		txd<<=1; 	  
		delay_us(2);   //对TEA5767这三个延时都是必须的
		IIC4_SCL(1);
		delay_us(4); 
   	IIC4_SCL(0);		
    }	
		IIC4_SDA(1);
}

u8 IIC1_Read_Byte(unsigned char ack)
{
	unsigned char i,receive=0;
	SDA1_IN();//SDA设置为输入
    for(i=0;i<8;i++ )
	 {    
        IIC1_SCL(0); 
        delay_us(4);
		    IIC1_SCL(1);
		    delay_us(2); 
        receive<<=1;
        if(READ_SDA1)receive++; 
		    delay_us(2); 
    }	
    IIC1_SCL(0); 
	  SDA1_OUT();      //SDA设置为输出 
		IIC1_SDA(0); 
    if (!ack)IIC1_NAck();//发送nACK
    else IIC1_Ack(); //发送ACK       
    return receive;
}


u8 IIC4_Read_Byte(unsigned char ack)
{
	unsigned char i,receive=0;
	SDA4_IN();//SDA设置为输入
    for(i=0;i<8;i++ )
	 {    
        IIC4_SCL(0); 
        delay_us(4);
		    IIC4_SCL(1);
		    delay_us(2); 
        receive<<=1;
        if(READ_SDA4)receive++; 
		    delay_us(2); 
    }	
    IIC4_SCL(0); 
	  SDA4_OUT();      //SDA设置为输出 
		IIC4_SDA(0); 
    if (!ack)IIC4_NAck();//发送nACK
    else IIC4_Ack(); //发送ACK       
    return receive;
}

u8 IIC1_Read_direct_bytes(u8 slaveadd,u8 *pBuffer,u16 NumToRead)
{	 
  __set_PRIMASK(1);	
  IIC1_Start();  
	IIC1_Send_Byte(slaveadd);      
	if(IIC1_Wait_Ack())
  {
	__set_PRIMASK(0);
	return 1;
	}
	IIC1_Start(); 
	IIC1_Send_Byte(slaveadd+1);           //进入接收模式			   
	if(IIC1_Wait_Ack())  
  {
	 __set_PRIMASK(0);
	 return 1;
	}
  while(NumToRead)
	{		
	 if(NumToRead==1)*pBuffer=IIC1_Read_Byte(0);
   else *pBuffer=IIC1_Read_Byte(1);
	 NumToRead--;	
	 pBuffer++;
	}
	IIC1_Stop();//产生一个停止条件	
	__set_PRIMASK(0);
	return 0;
} 

u8 IIC4_Read_direct_bytes(u8 slaveadd,u8 *pBuffer,u16 NumToRead)
{	 
  __set_PRIMASK(1);	
  IIC4_Start();  
	IIC4_Send_Byte(slaveadd);      
	if(IIC4_Wait_Ack())
  {
	__set_PRIMASK(0);
	return 1;
	}
	IIC4_Start(); 
	IIC4_Send_Byte(slaveadd+1);           //进入接收模式			   
	if(IIC4_Wait_Ack())  
  {
	 __set_PRIMASK(0);
	 return 1;
	}
  while(NumToRead)
	{		
	 if(NumToRead==1)*pBuffer=IIC4_Read_Byte(0);
   else *pBuffer=IIC4_Read_Byte(1);
	 NumToRead--;	
	 pBuffer++;
	}
	IIC4_Stop();//产生一个停止条件	
	__set_PRIMASK(0);
	return 0;
} 

u8 IIC1_ReadOneByte(u8 slaveadd,u16 ReadAddr,u8 double_address)
{				  
	u8 temp=0;	
  __set_PRIMASK(1);	
  IIC1_Start();  
	IIC1_Send_Byte(slaveadd);      
	IIC1_Wait_Ack();
  if(double_address)
	{		
  IIC1_Send_Byte(ReadAddr/256);   //发送高地址
	IIC1_Wait_Ack();
	}
  IIC1_Send_Byte(ReadAddr%256);   //发送低地址
	IIC1_Wait_Ack();
	IIC1_Start();  	 	   
	IIC1_Send_Byte(slaveadd+1);           //进入接收模式			   
	IIC1_Wait_Ack();	 
	temp=IIC1_Read_Byte(0);		   
	IIC1_Stop();//产生一个停止条件	 
	__set_PRIMASK(0);	
	return temp;
}


u8 IIC4_ReadOneByte(u8 slaveadd,u16 ReadAddr,u8 double_address)
{				  
	u8 temp=0;	
  __set_PRIMASK(1);	
  IIC4_Start();  
	IIC4_Send_Byte(slaveadd);      
	IIC4_Wait_Ack();
  if(double_address)
	{		
  IIC4_Send_Byte(ReadAddr/256);   //发送高地址
	IIC4_Wait_Ack();
	}
  IIC4_Send_Byte(ReadAddr%256);   //发送低地址
	IIC4_Wait_Ack();
	IIC4_Start();  	 	   
	IIC4_Send_Byte(slaveadd+1);           //进入接收模式			   
	IIC4_Wait_Ack();	 
	temp=IIC4_Read_Byte(0);		   
	IIC4_Stop();//产生一个停止条件	 
	__set_PRIMASK(0);	
	return temp;
}

u8 IIC1_Write_direct_bytes(u8 slaveadd,u8 *pBuffer,u16 NumToWrite)
{	
	__set_PRIMASK(1);	
  IIC1_Start();  
	IIC1_Send_Byte(slaveadd);   //发送器件地址0XA0,写数据 	 
	IIC1_Wait_Ack();		 
  while(NumToWrite)
	{		
	IIC1_Send_Byte(*pBuffer);     //发送字节							   
	if(IIC1_Wait_Ack())  
  {
	 __set_PRIMASK(0);
	 return 1;
	}
	NumToWrite--;
  pBuffer++;		
	}
  IIC1_Stop();//产生一个停止条件 
	delay_ms(5);
	__set_PRIMASK(0);
	return 0;
}

u8 IIC4_Write_direct_byte(u8 slaveadd,u8 cmd )
{	
	__set_PRIMASK(1);	
  IIC4_Start();  
	IIC4_Send_Byte(slaveadd);   //发送器件地址0XA0,写数据 	 
	IIC4_Wait_Ack();		 

	IIC4_Send_Byte(cmd);     //发送字节							   
	if(IIC4_Wait_Ack())  
  {
	 __set_PRIMASK(0);
	 return 1;
	}
  IIC4_Stop();//产生一个停止条件 
	delay_ms(5);
	__set_PRIMASK(0);
	return 0;
}


u8 IIC4_Write_direct_bytes(u8 slaveadd,u8 *pBuffer,u16 NumToWrite)
{	
	__set_PRIMASK(1);	
  IIC4_Start();  
	IIC4_Send_Byte(slaveadd);   //发送器件地址0XA0,写数据 	 
	IIC4_Wait_Ack();		 
  while(NumToWrite)
	{		
	IIC4_Send_Byte(*pBuffer);     //发送字节							   
	if(IIC4_Wait_Ack())  
  {
	 __set_PRIMASK(0);
	 return 1;
	}
	NumToWrite--;
  pBuffer++;		
	}
  IIC4_Stop();//产生一个停止条件 
	delay_ms(5);
	__set_PRIMASK(0);
	return 0;
}

u8 IIC1_WriteOneByte(u8 slaveadd,u16 WriteAddr,u8 DataToWrite,u8 double_address)
{	
	__set_PRIMASK(1);	
  IIC1_Start();  
	IIC1_Send_Byte(slaveadd);   //发送器件地址0XA0,写数据 	 
	IIC1_Wait_Ack();
  if(double_address)
	{		
  IIC1_Send_Byte(WriteAddr/256);   //发送高地址
	IIC1_Wait_Ack();
	}		
  IIC1_Send_Byte(WriteAddr%256);   //发送低地址
	IIC1_Wait_Ack(); 
	IIC1_Send_Byte(DataToWrite);     //发送字节							   
	IIC1_Wait_Ack(); 
  IIC1_Stop();//产生一个停止条件 
	delay_ms(5);
	__set_PRIMASK(0);
	return 0;
}

u8 IIC4_WriteOneByte(u8 slaveadd,u16 WriteAddr,u8 DataToWrite,u8 double_address)
{	
	__set_PRIMASK(1);	
  IIC4_Start();  
	IIC4_Send_Byte(slaveadd);   //发送器件地址0XA0,写数据 	 
	IIC4_Wait_Ack();
  if(double_address)
	{		
  IIC4_Send_Byte(WriteAddr/256);   //发送高地址
	IIC4_Wait_Ack();
	}		
  IIC4_Send_Byte(WriteAddr%256);   //发送低地址
	IIC4_Wait_Ack(); 
	IIC4_Send_Byte(DataToWrite);     //发送字节							   
	IIC4_Wait_Ack(); 
  IIC4_Stop();//产生一个停止条件 
	delay_ms(5);
	__set_PRIMASK(0);
	return 0;
}

u8 IIC1_Read_Nbytes(u8 slaveadd,u16 ReadAddr,u8 *pBuffer,u16 NumToRead,u8 double_address)
{	 
  __set_PRIMASK(1);	
  IIC1_Start();  
	IIC1_Send_Byte(slaveadd);      
	if(IIC1_Wait_Ack()) return 1;
  if(double_address)
	{		
  IIC1_Send_Byte(ReadAddr/256);   //发送高地址
	if(IIC1_Wait_Ack()) return 1;
	}
  IIC1_Send_Byte(ReadAddr%256);   //发送低地址
	if(IIC1_Wait_Ack()) return 1;
	IIC1_Start(); 
	IIC1_Send_Byte(slaveadd+1);           //进入接收模式			   
	if(IIC1_Wait_Ack()) return 1;
  while(NumToRead)
	{		
	 if(NumToRead==1)*pBuffer=IIC1_Read_Byte(0);
   else *pBuffer=IIC1_Read_Byte(1);
	 NumToRead--;	
	 pBuffer++;
	}
	IIC1_Stop();//产生一个停止条件	
	__set_PRIMASK(0);
	return 0;
}  


u8 IIC4_Read_Nbytes(u8 slaveadd,u16 ReadAddr,u8 *pBuffer,u16 NumToRead,u8 double_address)
{	 
  __set_PRIMASK(1);	
  IIC4_Start();  
	IIC4_Send_Byte(slaveadd);      
	if(IIC4_Wait_Ack()) return 1;
  if(double_address)
	{		
  IIC4_Send_Byte(ReadAddr/256);   //发送高地址
	if(IIC4_Wait_Ack()) return 1;
	}
  IIC4_Send_Byte(ReadAddr%256);   //发送低地址
	if(IIC4_Wait_Ack()) return 1;
	IIC4_Start(); 
	IIC4_Send_Byte(slaveadd+1);           //进入接收模式			   
	if(IIC4_Wait_Ack()) return 1;
  while(NumToRead)
	{		
	 if(NumToRead==1)*pBuffer=IIC4_Read_Byte(0);
   else *pBuffer=IIC4_Read_Byte(1);
	 NumToRead--;	
	 pBuffer++;
	}
	IIC4_Stop();//产生一个停止条件	
	__set_PRIMASK(0);
	return 0;
}  

u8 IIC1_Write_Nbytes(u8 slaveadd,u16 WriteAddr,u8 *pBuffer,u16 NumToWrite,u8 double_address)
{
	__set_PRIMASK(1);
	IIC1_Start();  
	IIC1_Send_Byte(slaveadd);   //发送器件地址0XA0,写数据 	 
	if(IIC1_Wait_Ack()) return 1;
  if(double_address)
	{		
  IIC1_Send_Byte(WriteAddr/256);   //发送高地址
	if(IIC1_Wait_Ack()) return 1;
	}		
  IIC1_Send_Byte(WriteAddr%256);   //发送低地址
	if(IIC1_Wait_Ack()) return 1;
  while(NumToWrite)
	{		
	IIC1_Send_Byte(*pBuffer);     //发送字节							   
	if(IIC1_Wait_Ack()) return 1;
	NumToWrite--;
  pBuffer++;		
	}		
  IIC1_Stop();//产生一个停止条件
  delay_ms(5); 
	__set_PRIMASK(0);
	return 0;
}

u8 IIC4_Write_Nbytes(u8 slaveadd,u16 WriteAddr,u8 *pBuffer,u16 NumToWrite,u8 double_address)
{
	__set_PRIMASK(1);
	IIC4_Start();  
	IIC4_Send_Byte(slaveadd);   //发送器件地址0XA0,写数据 	 
	if(IIC4_Wait_Ack()) return 1;
  if(double_address)
	{		
  IIC4_Send_Byte(WriteAddr/256);   //发送高地址
	if(IIC4_Wait_Ack()) return 1;
	}		
  IIC4_Send_Byte(WriteAddr%256);   //发送低地址
	if(IIC4_Wait_Ack()) return 1;
  while(NumToWrite)
	{		
	IIC4_Send_Byte(*pBuffer);     //发送字节							   
	if(IIC4_Wait_Ack()) return 1;
	NumToWrite--;
  pBuffer++;		
	}		
  IIC4_Stop();//产生一个停止条件
  delay_ms(5); 
	__set_PRIMASK(0);
	return 0;
}
