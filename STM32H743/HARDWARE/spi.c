#include "spi.h"


//以下是SPI模块的初始化代码，配置成主机模式 						  
//SPI口初始化
//这里针是对SPI2的初始化
void SPI1_Init(void)
{	 
	u32 tempreg=0;
	RCC->AHB4ENR|=1<<1;			//使能PORTB时钟 
	RCC->AHB4ENR|=1<<6;			//使能PORTG时钟 
	RCC->APB2ENR|=1<<12;		//SPI1时钟使能 
	GPIO_Set(GPIOG,1<<10,GPIO_MODE_OUT,GPIO_OTYPE_PP,GPIO_SPEED_FAST,GPIO_PUPD_PU); //PG10	输出
	GPIO_Set(GPIOG,5<<9,GPIO_MODE_AF,GPIO_OTYPE_PP,GPIO_SPEED_FAST,GPIO_PUPD_PU);	//PG9/11复用功能输出
  GPIO_Set(GPIOB,1<<5,GPIO_MODE_AF,GPIO_OTYPE_PP,GPIO_SPEED_FAST,GPIO_PUPD_PU);	//PB5复用功能输出	
	
  GPIO_AF_Set(GPIOB,5,5);	  //PB5,AF5
 	GPIO_AF_Set(GPIOG,9,5);	  //PG9,AF5
 	GPIO_AF_Set(GPIOG,11,5);	//PG11,AF5 
	//配置SPI的时钟源
	RCC->D2CCIP1R&=~(7<<12);//SPI123SEL[2:0]=0,清除原来的设置
	RCC->D2CCIP1R|=0<<12;		//SPI123SEL[2:0]=1,选择pll1_q_ck作为SPI1/2/3的时钟源,一般为100Mhz
								          //即:spi_ker_ck=100Mhz 
	//这里只针对SPI口初始化
	RCC->APB2RSTR|=1<<12;		//复位SPI1
	RCC->APB2RSTR&=~(1<<12);	//停止复位SPI1
	
	SPI1->CR1|=1<<12;			 //SSI=1,设置内部SS信号为高电平	
	SPI1->CFG1=7<<28;			 //MBR[2:0]=7,设置spi_ker_ck为256分频.
	SPI1->CFG1|=7<<0;			 //DSIZE[4:0]=7,设置SPI帧格式为8位,即字节传输
	tempreg=(u32)1<<31;		 //AFCNTR=1,SPI保持对IO口的控制
	tempreg|=0<<29;				 //SSOE=0,禁止硬件NSS输出
	tempreg|=1<<26;				 //SSM=1,软件管理NSS脚
	tempreg|=1<<25;				 //CPOL=1,空闲状态下,SCK为高电平
	tempreg|=1<<24;				 //CPHA=1,数据采样从第2个时间边沿开始
	tempreg|=0<<23;				 //LSBFRST=0,MSB先传输
	tempreg|=1<<22;				 //MASTER=1,主机模式
	tempreg|=0<<19;				 //SP[2:0]=0,摩托罗拉格式
	tempreg|=0<<17;				 //COMM[1:0]=0,全双工通信
	SPI1->CFG2=tempreg;		 //设置CFG2寄存器	
	SPI1->I2SCFGR&=~(1<<0);//选择SPI模式
	SPI1->CR1|=1<<0;			 //SPE=1,使能SPI1
 
	SPI1_ReadWriteByte(0xff);	//启动传输		 
}   

//以下是SPI模块的初始化代码，配置成主机模式 						  
//SPI口初始化
//这里针是对SPI2的初始化
void SPI2_Init(void)
{	 
	u32 tempreg=0;
	RCC->AHB4ENR|=1<<8;			//使能PORTI时钟 
	RCC->APB1LENR|=1<<14;		//SPI2时钟使能 
	GPIO_Set(GPIOI,1<<0,GPIO_MODE_OUT,GPIO_OTYPE_PP,GPIO_SPEED_FAST,GPIO_PUPD_PU);//	//PI0	输出
	GPIO_Set(GPIOI,7<<1,GPIO_MODE_AF,GPIO_OTYPE_PP,GPIO_SPEED_FAST,GPIO_PUPD_PU);	//PI1~3复用功能输出	
  GPIO_AF_Set(GPIOI,1,5);	//PI1,AF5
 	GPIO_AF_Set(GPIOI,2,5);	//PI2,AF5
 	GPIO_AF_Set(GPIOI,3,5);	//PI3,AF5 
	//配置SPI的时钟源
	RCC->D2CCIP1R&=~(7<<12);//SPI123SEL[2:0]=0,清除原来的设置
	RCC->D2CCIP1R|=0<<12;		//SPI123SEL[2:0]=1,选择pll1_q_ck作为SPI1/2/3的时钟源,一般为200Mhz
								//即:spi_ker_ck=200Mhz 
	//这里只针对SPI口初始化
	RCC->APB1LRSTR|=1<<14;		//复位SPI2
	RCC->APB1LRSTR&=~(1<<14);	//停止复位SPI2
	
	SPI2->CR1|=1<<12;			 //SSI=1,设置内部SS信号为高电平	
	SPI2->CFG1=7<<28;			 //MBR[2:0]=7,设置spi_ker_ck为256分频.
	SPI2->CFG1|=7<<0;			 //DSIZE[4:0]=7,设置SPI帧格式为8位,即字节传输
	tempreg=(u32)1<<31;		 //AFCNTR=1,SPI保持对IO口的控制
	tempreg|=0<<29;				 //SSOE=0,禁止硬件NSS输出
	tempreg|=1<<26;				 //SSM=1,软件管理NSS脚
	tempreg|=1<<25;				 //CPOL=1,空闲状态下,SCK为高电平
	tempreg|=1<<24;				 //CPHA=1,数据采样从第2个时间边沿开始
	tempreg|=0<<23;				 //LSBFRST=0,MSB先传输
	tempreg|=1<<22;				 //MASTER=1,主机模式
	tempreg|=0<<19;				 //SP[2:0]=0,摩托罗拉格式
	tempreg|=0<<17;				 //COMM[1:0]=0,全双工通信
	SPI2->CFG2=tempreg;		 //设置CFG2寄存器	
	SPI2->I2SCFGR&=~(1<<0);//选择SPI模式
	SPI2->CR1|=1<<0;			 //SPE=1,使能SPI2
 
	SPI2_ReadWriteByte(0xff);	//启动传输		 
}   

//以下是SPI模块的初始化代码，配置成主机模式 						  
//SPI口初始化
//这里针是对SPI2的初始化
void SPI4_Init(void)
{	 
	u32 tempreg=0;
	RCC->AHB4ENR|=1<<4;			  //使能PORTE时钟 
	RCC->APB2ENR|=1<<13;		  //SPI4时钟使能 
	GPIO_Set(GPIOE,1<<11,GPIO_MODE_OUT,GPIO_OTYPE_PP,GPIO_SPEED_FAST,GPIO_PUPD_PU); //E11
	GPIO_Set(GPIOE,7<<12,GPIO_MODE_AF,GPIO_OTYPE_PP,GPIO_SPEED_FAST,GPIO_PUPD_PU);	//E12~14复用功能输出	
	GPIO_Pin_Set(GPIOE,PIN11,1);
  GPIO_AF_Set(GPIOE,12,5);	//PE12,AF5
 	GPIO_AF_Set(GPIOE,13,5);	//PE13,AF5
 	GPIO_AF_Set(GPIOE,14,5);	//PE14,AF5 
	//配置SPI的时钟源
	RCC->D2CCIP1R&=~(7<<16);	//SPI45SEL[2:0]=0,清除原来的设置
	RCC->D2CCIP1R|=0<<16;		//SPI45SEL[2:0]=1,选择pll1_q_ck作为SPI4/5的时钟源,一般为200Mhz
								//即:spi_ker_ck=200Mhz 
	//这里只针对SPI口初始化
	RCC->APB2RSTR|=1<<13;		//复位SPI4
	RCC->APB2RSTR&=~(1<<13);	//停止复位SPI4
	
	SPI4->CR1|=1<<12;			//SSI=1,设置内部SS信号为高电平	
	SPI4->CFG1=7<<28;			//MBR[2:0]=7,设置spi_ker_ck为256分频.
	SPI4->CFG1|=15<<0;			//DSIZE[4:0]=15,设置SPI帧格式为16位,即半字传输
	tempreg=(u32)1<<31;			//AFCNTR=1,SPI保持对IO口的控制
	tempreg|=0<<29;				//SSOE=0,禁止硬件NSS输出
	tempreg|=1<<26;				//SSM=1,软件管理NSS脚
	tempreg|=1<<25;				//CPOL=1,空闲状态下,SCK为高电平
	tempreg|=0<<24;				//CPHA=1,数据采样从第2个时间边沿开始
	tempreg|=0<<23;				//LSBFRST=0,MSB先传输
	tempreg|=1<<22;				//MASTER=1,主机模式
	tempreg|=0<<19;				//SP[2:0]=0,摩托罗拉格式
	tempreg|=0<<17;				//COMM[1:0]=1,只发送
	SPI4->CFG2=tempreg;			//设置CFG2寄存器	
	SPI4->I2SCFGR&=~(1<<0);		//选择SPI模式
	SPI4->CR1|=1<<0;				//SPE=1,使能SPI4
  SPI4_SetSpeed(4);
	SPI4_ReadWriteByte(0xffff);	//启动传输		 
}   


//SPI1速度设置函数
//SpeedSet:0~7
//SPI速度=spi_ker_ck/2^(SpeedSet+1)
//spi_ker_ck我们选择来自pll1_q_ck,为200Mhz
void SPI1_SetSpeed(u8 SpeedSet)
{
	SpeedSet&=0X07;					//限制范围
 	SPI1->CR1&=~(1<<0); 			//SPE=0,SPI设备失能
	SPI1->CFG1&=~(7<<28); 			//MBR[2:0]=0,清除原来的分频设置
	SPI1->CFG1|=(u32)SpeedSet<<28;	//MBR[2:0]=SpeedSet,设置SPI2速度  
	SPI1->CR1|=1<<0; 				//SPE=1,SPI设备使能	 	  
}

//SPI2速度设置函数
//SpeedSet:0~7
//SPI速度=spi_ker_ck/2^(SpeedSet+1)
//spi_ker_ck我们选择来自pll1_q_ck,为200Mhz
void SPI2_SetSpeed(u8 SpeedSet)
{
	SpeedSet&=0X07;					//限制范围
 	SPI2->CR1&=~(1<<0); 			//SPE=0,SPI设备失能
	SPI2->CFG1&=~(7<<28); 			//MBR[2:0]=0,清除原来的分频设置
	SPI2->CFG1|=(u32)SpeedSet<<28;	//MBR[2:0]=SpeedSet,设置SPI2速度  
	SPI2->CR1|=1<<0; 				//SPE=1,SPI设备使能	 	  
} 

//SPI4速度设置函数
//SpeedSet:0~7
//SPI速度=spi_ker_ck/2^(SpeedSet+1)
//spi_ker_ck我们选择来自pll1_q_ck,为200Mhz
void SPI4_SetSpeed(u8 SpeedSet)
{
	SpeedSet&=0X07;					//限制范围
 	SPI4->CR1&=~(1<<0); 			//SPE=0,SPI设备失能
	SPI4->CFG1&=~(7<<28); 			//MBR[2:0]=0,清除原来的分频设置
	SPI4->CFG1|=(u32)SpeedSet<<28;	//MBR[2:0]=SpeedSet,设置SPI2速度  
	SPI4->CR1|=1<<0; 				//SPE=1,SPI设备使能	 	  
} 


//SPI1 读写一个字节
//TxData:要写入的字节
//返回值:读取到的字节
u8 SPI1_ReadWriteByte(u8 TxData)
{			 	   
	u8 RxData=0;	
	SPI1->CR1|=1<<0;				//SPE=1,使能SPI1
	SPI1->CR1|=1<<9;  				//CSTART=1,启动传输
	
	while((SPI1->SR&1<<1)==0);		//等待发送区空 
	*(vu8 *)&SPI1->TXDR=TxData;		//发送一个byte,以传输长度访问TXDR寄存器   
	while((SPI1->SR&1<<0)==0);		//等待接收完一个byte  
	RxData=*(vu8 *)&SPI1->RXDR;		//接收一个byte,以传输长度访问RXDR寄存器	
	
	SPI1->IFCR|=3<<3;				//EOTC和TXTFC置1,清除EOT和TXTFC位 
	SPI1->CR1&=~(1<<0);				//SPE=0,关闭SPI2,会执行状态机复位/FIFO重置等操作
	return RxData;					//返回收到的数据
}


//SPI2 读写一个字节
//TxData:要写入的字节
//返回值:读取到的字节
u8 SPI2_ReadWriteByte(u8 TxData)
{			 	   
	u8 RxData=0;	
	SPI2->CR1|=1<<0;				//SPE=1,使能SPI2
	SPI2->CR1|=1<<9;  				//CSTART=1,启动传输
	
	while((SPI2->SR&1<<1)==0);		//等待发送区空 
	*(vu8 *)&SPI2->TXDR=TxData;		//发送一个byte,以传输长度访问TXDR寄存器   
	while((SPI2->SR&1<<0)==0);		//等待接收完一个byte  
	RxData=*(vu8 *)&SPI2->RXDR;		//接收一个byte,以传输长度访问RXDR寄存器	
	
	SPI2->IFCR|=3<<3;				//EOTC和TXTFC置1,清除EOT和TXTFC位 
	SPI2->CR1&=~(1<<0);				//SPE=0,关闭SPI2,会执行状态机复位/FIFO重置等操作
	return RxData;					//返回收到的数据
}



//SPI4 读写一个字节
//TxData:要写入的字节
//返回值:读取到的字节
u16 SPI4_ReadWriteByte(u16 TxData)
{			 	   
	u16 RxData=0;	
	
	SPI4->CR1|=1<<0;				//SPE=1,使能SPI4
	SPI4->CR1|=1<<9;  	     //CSTART=1,启动传输	
	
	while((SPI4->SR&1<<1)==0);		//等待发送区空 
	SPI4->TXDR=TxData;		//发送2个byte,以传输长度访问TXDR寄存器   
	while((SPI4->SR&1<<0)==0);		//等待接收完一个byte  
	RxData=SPI4->RXDR;		//接收一个byte,以传输长度访问RXDR寄存器	
	
	SPI4->IFCR|=3<<3;				//EOTC和TXTFC置1,清除EOT和TXTFC位 
	SPI4->CR1&=~(1<<0);				//SPE=0,关闭SPI4,会执行状态机复位/FIFO重置等操作
	return RxData;					//返回收到的数据
}




