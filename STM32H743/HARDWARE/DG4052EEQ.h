#ifndef __DG4052EEQ_H_
#define __DG4052EEQ_H_

#include "sys.h"


#define  IO_SW5_A(x)       GPIO_Pin_Set(GPIOJ,PIN2,x)	
#define  IO_SW5_B(x)       GPIO_Pin_Set(GPIOJ,PIN3,x)	

void DG4052EEQ_Init(void);
void DG4052EEQ_Set(u8 set_res);
	
#endif
