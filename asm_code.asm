.data
  j_32 dd 0
  h_30 dd 0
  yy_28 dd 0
  y_26 dd 0
  b_24 dd 0
  t_22 dd 0
  a_20 dd 0
  j_17 dd 0
  y_15 dd 0
  g_13 dd 0
  b_11 dd 0
  d_9 dd 0
  hh_7 dd 0
  a_5 dd 0
  a_2 dd 0

.code
  mov [a_2], 78
  
  proc func1_3
    push ebp
    push esp
    push eax
    push ebx
    push ecx
    push edx
    push esi
    push edi
    mov [a_5], 9256
    mov [hh_7], -9222
    mov [d_9], 7
    mov [b_11], 3
    mov eax, [a_5]
    add eax, [d_9]
    mov ebx, eax
    add ebx, eax
    mov [g_13], ebx
    mov [y_15], eax
    mov eax, [b_11]
    add eax, [a_5]
    mov [j_17], eax
    mov eax, [a_5]
    sub eax, [d_9]
    mov [b_11], eax
    mov eax, [b_11]
    pop edi
    pop esi
    pop edx
    pop ecx
    pop ebx
    pop eax
    pop esp
    pop ebp
  endp func1_3
  
  proc func2_18
    push ebp
    push esp
    push eax
    push ebx
    push ecx
    push edx
    push esi
    push edi
    mov [a_20], 5
    mov [t_22], 6
    mov eax, [a_20]
    add eax, [t_22]
    mov ebx, eax
    add ebx, 2
    mov [b_24], ebx
    mov ebx, eax
    add ebx, 2
    mov eax, ebx
    add eax, 45
    mov ebx, eax
    add ebx, [a_20]
    mov [a_20], ebx
    mov eax, [a_20]
    add eax, [t_22]
    mov [y_26], eax
    mov ebx, [b_24]
    add ebx, [t_22]
    mov ecx, [a_20]
    add ecx, ebx
    mov ebx, ecx
    add ebx, 1
    mov [yy_28], ebx
    mov [h_30], eax
    mov [j_32], eax
    mov eax, 5
    pop edi
    pop esi
    pop edx
    pop ecx
    pop ebx
    pop eax
    pop esp
    pop ebp
  endp func2_18
  
  proc main_33
    push ebp
    push esp
    push eax
    push ebx
    push ecx
    push edx
    push esi
    push edi
    mov eax, 1
    pop edi
    pop esi
    pop edx
    pop ecx
    pop ebx
    pop eax
    pop esp
    pop ebp
  endp main_33
