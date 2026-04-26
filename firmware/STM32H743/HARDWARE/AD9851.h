#ifndef __AD9851_H_
#define __AD9851_H_

#include "sys.h"

#define IO_DDS1_RST(x)     GPIO_Pin_Set(GPIOH,PIN7,x)	
#define IO_DDS1_FQ_UD(x)   GPIO_Pin_Set(GPIOH,PIN8,x)	
#define IO_DDS1_W_CLK(x)   GPIO_Pin_Set(GPIOH,PIN9,x)	
#define IO_DDS1_D7(x)      GPIO_Pin_Set(GPIOH,PIN10,x)	


void AD9851_init(void);






#endif
