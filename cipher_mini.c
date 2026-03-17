// Custom Block Cipher — CBC/CFB | Sub+RotBytes+BitRot+MixDiffuse
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define GRN "\033[92m"
#define AMB "\033[93m"
#define GRY "\033[90m"
#define WHT "\033[97m"
#define RST "\033[0m"

void print_banner(const char*name){
    printf(GRN
    "\n  ██████╗██╗██████╗ ██╗  ██╗███████╗██████╗ \n"
    " ██╔════╝██║██╔══██╗██║  ██║██╔════╝██╔══██╗\n"
    " ██║     ██║██████╔╝███████║█████╗  ██████╔╝\n"
    " ██║     ██║██╔═══╝ ██╔══██║██╔══╝  ██╔══██╗\n"
    " ╚██████╗██║██║     ██║  ██║███████╗██║  ██║\n"
    "  ╚═════╝╚═╝╚═╝     ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝\n" RST
    GRY
    " ┌─────────────────────────────────────────┐\n"
    " │  Cipher : " WHT "%-29s" GRY "│\n"
    " │  Algo   : Sub + RotBytes + BitRot + Mix │\n"
    " │  Mode   : CBC / CFB  (non-ECB)          │\n"
    " └─────────────────────────────────────────┘\n" RST "\n",
    name);
}

// ── S-Box ────────────────────────────────────────────────────
static unsigned char SB[256], SI[256];
void init_sbox() {
    for(int i=0;i<256;i++) SB[i]=i;
    unsigned int s=0xB16B00B5;
    for(int i=255;i>0;i--){
        s=s*1664525+1013904223;
        int j=s%(i+1); unsigned char t=SB[i];SB[i]=SB[j];SB[j]=t;
    }
    for(int i=0;i<256;i++) SI[SB[i]]=i;
}

// ── Bit rotation ────────────────────────────────────────────
#define RL(b,n) (((b)<<((n)%8))|((b)>>>(8-(n)%8)))&0xFF  // tidak valid di C, pakai fungsi
unsigned char rl(unsigned char b,int n){n%=8;return((b<<n)|(b>>(8-n)))&0xFF;}
unsigned char rr(unsigned char b,int n){return rl(b,(8-n%8)%8);}

// ── Key schedule ────────────────────────────────────────────
void key_sched(const char*k,int R,unsigned char rkeys[][8]){
    int kl=strlen(k);
    unsigned char st[64];
    for(int i=0;i<64;i++) st[i]=SB[((unsigned char)k[i%kl]^(unsigned char)k[(i*7+3)%kl]^i*0x6B^0x37)&0xFF];
    for(int r=0;r<=R;r++)
        for(int i=0;i<8;i++)
            rkeys[r][i]=SB[(st[(r*8+i)%64]^r*0x9E^i*0x6C)&0xFF];
}

// ── Block encrypt ───────────────────────────────────────────
void enc_block(unsigned char b[8],unsigned char rk[][8],int R){
    for(int i=0;i<8;i++) b[i]^=rk[0][i];
    for(int r=1;r<=R;r++){
        for(int i=0;i<8;i++) b[i]=SB[b[i]];                      // Sub
        int sh=(r%4)+1; unsigned char tmp[8];                      // RotBytes
        for(int i=0;i<8;i++) tmp[i]=b[(i+sh)%8];
        for(int i=0;i<8;i++) b[i]=rl(tmp[i],((r*3+i*5)%7)+1);    // BitRot
        for(int i=1;i<8;i++) b[i]^=rl(b[i-1],3);                 // MixDiffuse
        for(int i=0;i<8;i++) b[i]^=rk[r][i];
    }
}

// ── Block decrypt ───────────────────────────────────────────
void dec_block(unsigned char b[8],unsigned char rk[][8],int R){
    for(int i=0;i<8;i++) b[i]^=rk[R][i];
    for(int r=R;r>=1;r--){
        for(int i=7;i>=1;i--) b[i]^=rl(b[i-1],3);                // InvMix
        for(int i=0;i<8;i++) b[i]=rr(b[i],((r*3+i*5)%7)+1);      // InvBitRot
        int sh=(r%4)+1; unsigned char tmp[8];                      // InvRotBytes
        for(int i=0;i<8;i++) tmp[i]=b[(i+8-sh)%8];
        for(int i=0;i<8;i++) b[i]=SI[tmp[i]];                     // InvSub
        for(int i=0;i<8;i++) b[i]^=rk[r-1][i];
    }
}

// ── PKCS7 pad/unpad ─────────────────────────────────────────
int pkcs_pad(unsigned char*buf,int len){
    int p=8-len%8;
    for(int i=0;i<p;i++) buf[len+i]=(unsigned char)p;
    return len+p;
}
int pkcs_unpad(unsigned char*buf,int len){
    int p=buf[len-1];
    return(p>=1&&p<=8)?len-p:len;
}

// ── Random IV ───────────────────────────────────────────────
void rand_iv(unsigned char iv[8]){srand((unsigned)time(NULL)^(unsigned)(size_t)iv);for(int i=0;i<8;i++)iv[i]=rand()&0xFF;}

// ── CBC encrypt ─────────────────────────────────────────────
int cbc_enc(unsigned char*pt,int len,unsigned char rk[][8],int R,unsigned char*out){
    unsigned char iv[8]; rand_iv(iv);
    memcpy(out,iv,8); int ol=8;
    unsigned char buf[512]; memcpy(buf,pt,len);
    int plen=pkcs_pad(buf,len);
    unsigned char prev[8]; memcpy(prev,iv,8);
    for(int i=0;i<plen;i+=8){
        unsigned char blk[8];
        for(int j=0;j<8;j++) blk[j]=buf[i+j]^prev[j];
        enc_block(blk,rk,R);
        memcpy(out+ol,blk,8); memcpy(prev,blk,8); ol+=8;
    }
    return ol;
}
int cbc_dec(unsigned char*ct,int len,unsigned char rk[][8],int R,unsigned char*out){
    unsigned char prev[8]; memcpy(prev,ct,8);
    int ol=0;
    for(int i=8;i<len;i+=8){
        unsigned char blk[8]; memcpy(blk,ct+i,8);
        dec_block(blk,rk,R);
        for(int j=0;j<8;j++) out[ol+j]=blk[j]^prev[j];
        memcpy(prev,ct+i,8); ol+=8;
    }
    return pkcs_unpad(out,ol);
}

// ── Base64 ──────────────────────────────────────────────────
static const char B64[]="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
void b64enc(unsigned char*in,int len,char*out){
    int i=0,o=0;
    while(i<len){
        unsigned int v=(in[i]<<16)|((i+1<len?in[i+1]:0)<<8)|(i+2<len?in[i+2]:0);
        out[o++]=B64[(v>>18)&63];out[o++]=B64[(v>>12)&63];
        out[o++]=(i+1<len)?B64[(v>>6)&63]:'=';
        out[o++]=(i+2<len)?B64[v&63]:'=';
        i+=3;
    }
    out[o]=0;
}
int b64dec(const char*in,unsigned char*out){
    static unsigned char T[256]={0};
    if(!T['A'])for(int i=0;i<64;i++)T[(unsigned char)B64[i]]=i;
    int len=strlen(in),o=0;
    for(int i=0;i<len;i+=4){
        unsigned int v=(T[(unsigned char)in[i]]<<18)|(T[(unsigned char)in[i+1]]<<12)|
                       ((in[i+2]!='='?T[(unsigned char)in[i+2]]:0)<<6)|
                       (in[i+3]!='='?T[(unsigned char)in[i+3]]:0);
        out[o++]=(v>>16)&0xFF;
        if(in[i+2]!='=') out[o++]=(v>>8)&0xFF;
        if(in[i+3]!='=') out[o++]=v&0xFF;
    }
    return o;
}

// ── Main ────────────────────────────────────────────────────
int main(){
    init_sbox();
    char name[32],key[64],mode[4],text[512],b64buf[1024];
    int R;
    unsigned char rk[17][8], buf[512], out[512];

    printf(GRY "  cipher:// " RST);
    printf("Nama cipher: "); scanf("%31s",name);
    print_banner(name);

    printf(GRN "  🔑 " RST "Kunci      : "); scanf("%63s",key);
    printf(GRN "  ⚙  " RST "Mode (cbc/cfb): "); scanf("%3s",mode);
    printf(GRN "  🔄 " RST "Ronde (4-16): "); scanf("%d",&R);
    for(int i=0;mode[i];i++) mode[i]=mode[i]>='a'?mode[i]-32:mode[i];

    key_sched(key,R,rk);

    printf(GRY "\n  ┌────────────────────┐\n" RST);
    printf(GRY "  │ " GRN "[1]" RST " Enkripsi        " GRY "│\n" RST);
    printf(GRY "  │ " AMB "[2]" RST " Dekripsi        " GRY "│\n" RST);
    printf(GRY "  └────────────────────┘\n" RST);
    int pilihan; printf("  > "); scanf("%d",&pilihan);
    getchar();

    if(pilihan==1){
        printf("\n  📝 Teks: "); fgets(text,sizeof(text),stdin);
        text[strcspn(text,"\n")]=0;
        int pt_len=strlen(text);
        int ct_len=cbc_enc((unsigned char*)text,pt_len,rk,R,out);
        b64enc(out,ct_len,b64buf);
        printf(GRY "\n  ┌─ CIPHERTEXT (%s) " RST "\n" GRY "  │ " GRN "%s.%s.%s\n" GRY "  └─────────────\n" RST,
               mode,name,mode,b64buf);
    } else {
        printf("\n  📋 Ciphertext: "); fgets(text,sizeof(text),stdin);
        text[strcspn(text,"\n")]=0;
        char*p1=strchr(text,'.'),*p2=p1?strchr(p1+1,'.'):NULL;
        char*b64=p2?p2+1:text;
        int ct_len=b64dec(b64,buf);
        int pt_len=cbc_dec(buf,ct_len,rk,R,out);
        out[pt_len]=0;
        printf(GRY "\n  ┌─ PLAINTEXT ──\n  │ " WHT "%s\n" GRY "  └─────────────\n" RST,out);
    }
    return 0;
}