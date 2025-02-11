!+
!PROGRAM TND2897
! ---------------------------------------------------------------------------
! PURPOSE -
! AUTHORS - Virginia L. Sorenson, NASA Ames Research Center
!           Ralph L. Carmichael, Public Domain Aeronautical Software
! REVISION HISTORY
!   DATE  VERS PERSON  STATEMENT OF CHANGES
!   1965   1.0   VLS   Original coding at NASA/Ames
! 21Jul97  1.1   RLC   Scanned program from printed report
! 28Dec99  1.2   RLC   Reordered /blank/ to put reals first, integers next
!                       also no text strings on STOP statements
! 30Mar09  1.3   RLC   Reordered to put all procedures in  modules


!+
MODULE CONSTANTS
! ------------------------------------------------------------------------------
! PURPOSE - 

  INTEGER,PARAMETER:: SP=KIND(1.0), DP=KIND(1.0D0)   ! Numerical Recipes
  INTEGER,PARAMETER:: FIG=3, DBG=4
  REAL(DP),PARAMETER:: PI=3.14159265
!-------------------------------------------------------------------------------

END Module Constants   ! =======================================================
!+
MODULE Blank
! ------------------------------------------------------------------------------
! PURPOSE -

!+
! PURPOSE - Definition of common block /BLANK/
!
! Reordered 28 Dec 99  RLC to put the reals(DP) first and
!  the integers second (DPs should be on 8-byte boundaries)

USE Constants

      INTEGER:: i,itype,ireg,iray,ifam,in,j,jp,k,kp
      INTEGER,DIMENSION(2,9):: icon
      INTEGER,DIMENSION(2,4)::nop
      INTEGER:: noa,nob
      INTEGER:: last
      REAL(DP),DIMENSION(2,4,50):: x,r,del,w,s,u
      REAL(DP):: gamma,test,crmax,scb,san,p4
      REAL(DP):: sing,xt,theta,emin,win
      REAL(DP),DIMENSION(3,50):: atab,ctab
      REAL(DP):: coalt
      REAL(DP):: xin,thetb,space

      INTEGER,DIMENSION(9):: irr
      EQUIVALENCE (irr(1),itype)
      EQUIVALENCE (irr(2),ireg)
      EQUIVALENCE (irr(3),iray)
      EQUIVALENCE (irr(4),ifam)
      EQUIVALENCE (irr(5),in)
      EQUIVALENCE (irr(6),j)
      EQUIVALENCE (irr(7),jp)
      EQUIVALENCE (irr(8),k)
      EQUIVALENCE (irr(9),kp)


!      COMMON /BLANK/x,r,del,w,s,u,   gamma,test,crmax,scb,san,p4,  &
!        sing,xt,theta,emin,win, atab,ctab, coalt, xin,thetb,space, &
!       itype,ireg,iray,ifam,in,j,jp,k,kp,          &
!        icon,i,nop,noa,nob,last

END Module Blank   ! ===========================================================

!+
MODULE InletProcedures
! ------------------------------------------------------------------------------

USE Constants
IMPLICIT NONE

  CHARACTER(LEN=80):: generalTitle


!----------------------------------------------------------------------------


CONTAINS

!+
SUBROUTINE Acray(dai,wup,sup,dup,xb,rb)
! ---------------------------------------------------------------------------
! PURPOSE - Computes a two-dimensional input ray
!
! NOTES - Called only from main program
!!!  INCLUDE 'blank.cmn'
  USE Blank

  REAL(DP),INTENT(IN):: dai
  REAL(DP),INTENT(IN):: wup,sup,dup
  REAL(DP),INTENT(IN):: xb
  REAL(DP),INTENT(IN OUT):: rb


  REAL(DP):: spacc
  COMMON /SPACC/SPACC

  REAL(DP):: argXXX
  REAL(DP),DIMENSION(4):: co
  REAL(DP):: dink
  REAL(DP):: dr
  REAL(DP):: dx
  REAL(DP):: em,emup
  REAL(DP):: g1,g3,g4,g5
  REAL(DP):: rs
  REAL(DP):: t1,t2,t3,t4,t5
  REAL(DP):: t,ta,tb
  REAL(DP):: uup
  REAL(DP):: z

!----------------------------------------------------------------------------
write(DBG,*) "Entering Acray", dai,wup,sup,dup,xb,rb,ireg

   K=1
   write(DBG,*) "k set to 1 in Acray"
   IF (IREG-2) 37,38,3
38 IF (SPACC .LE. 0.) SPACC=0.5
   DX=SPACE*SPACC
   GO TO 39

37 X(I,J,K)=XB       ! only way to get here is if IREG < 2.   Impossible???
   DX=XB
   RB=0.0
   WRITE(DBG,*) "IREG < 2 in Acray"
   WRITE(*,*) "IREG < 2 in Acray"    ! Announce it on screen
   GO TO 34

 3 DX=0.75*SPACE
39 SPACE=DX
 4 X(I,J,K)=XB+DX

   IF (X(I,J,K) > XT) THEN
     CALL PUNT(3)
     RETURN
   END IF

34 T=1.0
   GO TO (1,2),IFAM
 2 T=-T


 1 R(I,J,K)=RB+DX*TAN(DAI)
!!!   TB=SQRT(1.0-0.5*(GAMMA-1.0)*WUP**2)/WUP
   argXXX=1.0-0.5*(GAMMA-1.0)*WUP**2
   WRITE(DBG,*) "In Acray, argXXX=", argXXX, wup
   tb=SQRT(argXXX)/wup

   UUP=ASIN(TB)    ! never used ?????????
   EMUP=1.0/TB
   G1=EMUP**2
   G3=(G1+2.0)/G1
   G4=(2.0*G1+1.0)/G1**2
   G5=(GAMMA+1.0)**2/4.0+(GAMMA-1.0)/G1
   DEL(I,J,K)=DAI
   T1=SIN(ABS(DUP-DAI ))**2

   write(DBG,*) "In Acray, preparing to call cubic", tb,emup,g1,g3,g4,g5,t1
   CO(1)=(T1-1.0)/G1**2
   CO(2)=G4+G5*T1
   CO(3)=-G3-GAMMA*T1
   CO(4)=1.0
write(DBG,*) "Calling Cubic from Acray", co
   CALL CUBIC(co(:),Z)                        ! returns z

   T2=(2.0*GAMMA*G1*Z-GAMMA+1.0)/(GAMMA+1.0)
   IF (t2 <= 0.0) THEN
     WRITE(DBG,*) "t2 non-positive in Acray"
     CALL ErrorMessage(13)
     RETURN
   END IF

   T3=(GAMMA+1.0)*G1*Z/((GAMMA-1.0)*G1*Z+2.0)
   IF (t3 <= 0.0) THEN
     WRITE(DBG,*) "t3 non-positive in Acray"
     CALL ErrorMessage(13)
     RETURN
   END IF

   S(I,J,K)=SUP+(LOG(T2)-GAMMA*LOG(T3))/(GAMMA-1.0)

   T4=1.0-4.0*(G1*Z-1.0)/Z*(GAMMA*G1*Z+1.0)/((GAMMA+1.0)*G1)**2
   IF (t4 < 0.0) THEN
     WRITE(DBG,*) "t4 negative in Acray"
     CALL ErrorMessage(14)
     RETURN
   END IF

   W(I,J,K)=WUP*SQRT(T4)

   TA=1.0-0.5*(GAMMA- 1.0)*W(I,J,K)**2
   IF (ta <= 0.0) THEN
     WRITE(DBG,*) "ta non-positive in Acray"
     CALL ErrorMessage(14)
     RETURN
   END IF

   EM=W(I,J,K)/SQRT(TA)
   IF (em <= 1.0) THEN
     WRITE(DBG,*) "Flow has gone subsonic. Mach=", em
     CALL ErrorMessage(15)
     RETURN
   END IF
   IF (em > emup) THEN
     WRITE(DBG,*) "Mach number is greater that free stream. Mach=", em
     CALL ErrorMessage(15)
     RETURN
   END IF

!!!13 CALL ErrorMessage(15)
!!!    RETURN

   IF (z <= 0.0) THEN
     WRITE(DBG,*) "Non-positive return from Cubic. z=",z
     CALL ErrorMessage(15)
     RETURN
   END IF

   T5=SQRT(Z)
   IF (T5 > 1.0) THEN
     WRITE(DBG,*) "T5 greater than 1 in Acray. T1=", t1
     CALL ErrorMessage(15)
     RETURN
   END IF

   THETA=ASIN(T5)
   RS=RB+T*DX*TAN(THETA+T*DUP)
   DINK=IN-1                     ! convert integer to real
   DR=(RS-R(I,J,K))/DINK
   GO TO (17,18),IFAM
17 SCB=S(I,J,K)
   GO TO 16
18 SAN=S(I,J,K)

16 CALL PUNT(1)
   K=K+1
   write(DBG,*) "k incremented in Acray. Now=", k
   X(I,J,K)=X(I,J,K-1)
   R(I,J,K)=R(I,J,K-1)+DR
   DEL(I,J,K)=DEL(I,J,K-1)
   W(I,J,K)=W(I,J,K-1)
   S(I,J,K)=S(I,J,K-1)
   IF (K < IN) GO TO 16

19 NOP(I,J)=IN
   CALL PUNT(1)
   WRITE(DBG,*) "Leaving Acray"
   RETURN
END Subroutine Acray   ! ----------------------------------------------------

!+
SUBROUTINE Body(fun,tab,max)
! ---------------------------------------------------------------------------
! PURPOSE - Computes a body point
!
! NOTES - Called from main program and UpSc
USE Blank

  INTERFACE
    SUBROUTINE fun(i,a,b,c)
      INTEGER,INTENT(IN):: i
      REAL(KIND=8),INTENT(IN):: a
      REAL(KIND=8),INTENT(OUT):: b,c
    END Subroutine fun
  END INTERFACE

  REAL(DP),INTENT(IN),DIMENSION(:,:):: tab
  INTEGER,INTENT(IN):: max

  INTEGER:: idim
  COMMON/DIM/idim
!!!  INCLUDE 'blank.cmn'

  REAL(DP):: a2
  REAL(DP):: c2
  REAL(DP):: d2
  REAL(DP):: dr
  REAL(DP):: cor2
  REAL(DP):: gan
  REAL(DP):: gpan
  INTEGER:: icow
  INTEGER:: iter
  INTEGER:: kpp1
!  INTEGER:: loopVar
  INTEGER:: lp
  REAL(DP):: ra2
  REAL(DP):: ratio
  REAL(DP):: t1
  REAL(DP):: tana2
  REAL(DP):: wprev

  REAL(DP):: t

!----------------------------------------------------------------------------
  WRITE(DBG,*) "Entering Body"

  KPP1=KP+1
  IF (K-1) 3,3,4
    3 GO TO (5,6),IFAM
    5 S(I,J,K)=SCB
    T=1.0
    GO TO 7
    4 KP=KP-1
    KPP1=KP+1
    GO TO (6,5),IFAM
    6 S(I,J,K)=SAN
    T=-1.0

    7 DO 8 ITER=1,25
    X(I,J,K)=X(I,JP,KPP1)
    IF (max <= 0) GO TO 10

11 DO LP=2,MAX
     IF (X(I,J,K) >= TAB(1,LP)) CYCLE
  36 A2=U(I,JP,KPP1)- DEL(I,JP,KPP1)*T
     TANA2=TAN(A2)
     T1=(TAB(2,LP)-TAB(2,LP-1))/(TAB(1,LP)-TAB(1,LP-1))
     X(I,J,K)=(R(I,JP,KPP1)-TAB(2,LP-1)+ &
        (X( I,JP,KPP1)*T)*TANA2+TAB(1,LP-1)*T1)/(TANA2*T+T1)
     IF (X(I,J,K) <= TAB(1,LP)) GO TO 37
   END DO   

  CALL PUNT(3)
  RETURN

37 R(I,J,K)=R(I,JP,KPP1)-TANA2*T*(X(I,J,K)-X(I,JP,KPP1))
   DEL(I,J,K)=TAB(3,LP-1)*.017453293
   GO TO 1

10 A2=U(I,JP,KPP1)-DEL(I,JP,KPP1)*T
   TANA2=TAN(A2)
   DO 9 ICOW=1,25
     CALL FUN(2,X(I,J,K),R(I,J,K),DR)   ! was statement #12
     T1=(X(I,J,K)-X(I,JP,KPP1))+TANA2
     GAN=R(I,J,K)-R(I,JP,KPP1)+T1*T
     GPAN=DR+TANA2*T
     IF (ABS(GPAN) < 1.E-15) THEN
       CALL ErrorMessage(2)
       RETURN
     END IF
  14 RATIO=GAN/GPAN
     X(I,J,K)=X(I,J,K)-RATIO
     IF (ABS(RATIO)- TEST ) 15,15,9
  15 IF (X(I,J,K)-XT) 41,41,40
 9 END DO
   GO TO 2

40 CALL PUNT(3)
   RETURN

41 CALL FUN(2,X(I,J,K),R(I,J,K),DR)
   DEL(I,J,K)=ATAN(DR)
 1 C2=0.0
   COR2=(R(I,JP,KPP1)-R(I,J,K))/R(I,JP,KPP1)/SIN(A2)
   COR2=ABS(COR2)
   GO TO (33,33,31),IDIM
31 C2=COR2*SIN(U(I,JP,KPP1))*SIN(DEL(I,JP,KPP1))  ! why 31
33 RA2=W(I,JP,KPP1)*TAN(U(I,JP,KPP1))
   D2=0.5*SIN(2.0*U(I,JP,KPP1))/GAMMA
   IF (DEL(I,J,K)> 0.5*PI) THEN
     CALL ErrorMessage(3)
     RETURN
   END IF

17 W(I,J,K)=W(I,JP,KPP1)+C2*RA2-D2*RA2*(S(I,J,K)-S(I,JP,KPP1))
   T1=(DEL(I,JP,KPP1)-DEL(I,J,K))*RA2
   W(I,J,K)=W(I,J,K)+ T1*T
   IF (ITER-1) 2,18,19
18 IF (COR2-CRMAX) 20,20,21
21 CALL JUGGLE(2)
   GO TO 22
19 IF (ABS(W(I,J,K)-WPREV)-TEST) 23,23,22
23 CALL JUGGLE(8)
20 IF (K .EQ. 1) GO TO 25
26 KP=KP+1

25 IF (IFAM <= 1) THEN
     CALL PUNT( 8)
   ELSE
     CALL PUNT( 9)
   END IF
   WRITE(DBG,*) "Normal return from Body"
   RETURN

22 WPREV=W(I,J, K )
   CALL JUGGLE(5)
 8 CONTINUE
   CALL ErrorMessage(4)
   RETURN
 2 CALL ErrorMessage(2)
   RETURN
END Subroutine Body     ! -------------------------------------------------------

!+
SUBROUTINE BsInt(vbody,tab,no,xb,rb,slosh,xint,rint)
! ---------------------------------------------------------------------------
! PURPOSE - Compute the intersection of a shock wave with either the
!   centerbody or cowl.

! NOTES - Called from Shock
USE Blank
  IMPLICIT NONE

  INTERFACE
    SUBROUTINE vbody(ii,a,b,c)
      INTEGER,PARAMETER:: DP=KIND(1.0D0)
      INTEGER,INTENT(IN):: ii
      REAL(DP),INTENT(IN):: a
      REAL(DP),INTENT(OUT):: b,c
    END Subroutine vbody
  END INTERFACE

  REAL(DP),INTENT(IN),DIMENSION(:,:):: tab
  INTEGER,INTENT(IN):: no
  REAL(DP),INTENT(IN):: xb,rb
  REAL(DP),INTENT(IN):: slosh
  REAL(DP),INTENT(OUT):: xint,rint

!!!  INCLUDE 'blank.cmn'

  REAL(DP),PARAMETER:: EPS=1.0E-6

  REAL(DP):: drv
  INTEGER:: ip,ix
  REAL(DP):: gpx
  REAL(DP):: gx
  REAL(DP):: rv
  REAL(DP):: slop1
  REAL(DP):: xv
!----------------------------------------------------------------------------
write(DBG,*) "Entering BsInt"

  IF (no == 1) THEN
    XV=XB
    DO IX=1,25
      CALL VBODY(2,XV,RV,DRV)
      GX=RV-RB-(XV-XB)*SLOSH
      GPX=DRV-SLOSH
      IF (ABS(GPX) < EPS) THEN
        CALL ErrorMessage(18)
        RETURN
      END IF
      XV=XV-GX/GPX
      IF (ABS(GX/GPX) < EPS) THEN
        xint=xv
        rint=rb+(xint-xb)*slosh
        RETURN
      END IF
    END DO
    CALL ErrorMessage(18)   ! if you complete the loop, you are toast
    RETURN
  ELSE
    DO IP=2,NO
!        IP=IP
      IF (XB <= TAB(I,IP)) EXIT
    END DO

 8 SLOP1=(TAB(2,IP)-TAB(2,IP-1))/(TAB(1,IP)-TAB(1,IP-1))
   XINT=(SLOP1*TAB(1,IP)-XB*SLOSH-TAB(2,IP)+RB)/(SLOP1-SLOSH)
   IF (XINT-TAB(1,IP)) 9,9,10
10 IP=IP+I
   IF (IP <= NO) GO TO 8

 9 RINT=TAB(2,IP)+(XINT-TAB(1,IP))*SLOP1
  END IF
  WRITE(DBG,*) "Normal return from BsInt"
  RETURN
END Subroutine BsInt   ! -------------------------------------------------------

!+
SUBROUTINE Conic()
! ---------------------------------------------------------------------------
! PURPOSE - Start a new conical region
!
! NOTES - Called from main program
USE Blank
!!!  INCLUDE 'blank.cmn'
  CHARACTER(LEN=*),PARAMETER:: FMT101= "(7F10.6)"

  REAL(DP):: ddm
  REAL(DP):: delbd
  REAL(DP):: delsh
  REAL(DP):: div
  REAL(DP):: dm
  REAL(DP):: drm
  REAL(DP):: ds
  REAL(DP):: embod
  REAL(DP):: emsh
  REAL(DP):: g1
  INTEGER:: nopin
  REAL(DP):: opin
  REAL(DP):: rb
  REAL(DP):: rm
  REAL(DP):: t2,t3
  REAL(DP):: wdm
  REAL(DP):: wm
  REAL(DP):: xb
  REAL(DP):: z
!----------------------------------------------------------------------------
write(DBG,*) "Entering Conic"  
  READ(5,FMT101) XB,RB ,EMSH,EMBOD,DELSH,DELBD, OPIN
  NOPIN=OPIN

write(DBG,*) xb,rb,emsh,embod,delsh,delbd,nopin
  
  XIN=XB
  IF (nopin > 0) THEN
    in=nopin
  ELSE
    in=2
    nopin=2
  END IF

  NOP(I,J)=IN
  ITYPE=1
  write(DBG,*) "ITYPE set to 1 in Conic"
  K=1
  write(DBG,*) "k set to 1 in Conic"
  X(I,J,K)=XB
  R(I,J,K)=RB
  DEL(I,J,K)=0.01745329*DELBD
  W(I,J,K)=EMBOD/SQRT(0.5*(GAMMA-1.0)*EMBOD**2+1.0)    ! Eq. 16
  Z=SIN(THETA)**2
  G1=EMIN**2
  T2=(2.0*GAMMA*G1*Z-GAMMA+1.0)/(GAMMA+1.0)
1 T3=(GAMMA+1.0)*G1*Z/((GAMMA-1.0)*G1*Z+2.0)

  IF (t2<=0.0  .OR.  t3<=0.0) THEN
    CALL ErrorMessage(11)
    RETURN
  END IF

!!!      IF (T2) 2,2,3
!!!    3 IF (T3) 2,2,7
!!!    2 CALL ErrorMessage(11)
!!!      RETURN

  DS= (LOG(T2)-GAMMA*LOG(T3))/(GAMMA-1.0)
  IF (ds < 0.0) ds=0.0
  S(I,J,K)=SING+DS                                        ! Eq 15
  SCB=S(I,J,K)
  CALL PUNT(8)
  RM=XB*TAN(THETA)
  DIV=NOPIN-1       ! converts integer to real
  DRM=(RM-R(I,J,K))/DIV

  DM=0.01745329*DELSH

  WM=EMSH/SQRT(0.5*(GAMMA-1.0)*EMSH**2+1.0)
  DDM=(DM-DEL(I,J,K))/DIV
  WDM=(WM-  W(I,J,K))/DIV

  DO K=2,NOPIN              ! interpolate additional points
   !!! K=K
    X( I,J,K)=XB
    S(I,J,K)=S(I,J,K-1)
    W(I,J,K)=W(I,J,K-1)+WDM
    R(I,J,K)=R(I,J,K-1)+DRM
    DEL(I,J,K)=DEL(I,J,K-1)+DDM
    CALL PUNT(1)
  END DO
  WRITE(DBG,*) "Normal return from Conic"
  RETURN
END Subroutine Conic   ! -------------------------------------------------------

!+
SUBROUTINE Cubic(c,z)
! ---------------------------------------------------------------------------
! PURPOSE - Finds roots of a cubic and selects the proper root for the
!   shock wave equation
!
! NOTES - Called from Shock and Acray
  IMPLICIT NONE

  REAL(DP),INTENT(IN),DIMENSION(:):: c
  REAL(DP),INTENT(OUT):: z

  REAL(DP):: p,q,rsq,phi,tem
  REAL(DP):: x1,x2,x3,y1
!----------------------------------------------------------------------------
  write(DBG,'(A,4ES15.4)') "Entering Cubic", c

  P=-C(3)**2/3.0 + C(2)
  Q=2.0*c(3)**3/27.0 - C(2)*C(3)/3.0 + C(1)
  RSQ=-0.5*Q/SQRT(-P**3/27.0)

  IF (ABS(RSQ) > 1.0) RSQ=SIGN(1.0D0,RSQ)
  PHI=ACOS(RSQ)
  TEM=2.0*SQRT(-P/3.0)
  X1= TEM*COS(PHI/3.0)
  X2= TEM*COS(PHI/3.0 + 2.09439510)
  X3= TEM*COS(PHI/3.0 + 4.18879020)
  IF (x2 > x3) THEN   ! get the middle value of { x1,x2,x3 }
    y1=MIN(x1,x2)
    y1=MAX(y1,x3)
  ELSE
    y1=MAX(x1,x2)
    y1=MIN(y1,x3)
  END IF
  z=y1-c(3)/3.0

  IF (z > 1.0) THEN
    WRITE(*,*) "z > 1 computed by Cubic. Set to 1.0"
    WRITE(DBG,*) "z > 1 computed from Cubic. Set to 1.0"
    z=1.0
    WRITE(DBG,*) c
    WRITE(DBG,*) p,q,rsq,phi,tem
    WRITE(DBG,*) x1,x2,x3
  END IF

  WRITE(DBG,*) "Leaving Cubic"
  RETURN
END Subroutine Cubic   ! ----------------------------------------------------

!+
SUBROUTINE Endfil()
! ---------------------------------------------------------------------------
! PURPOSE - End of file handler
!
!----------------------------------------------------------------------------
!!!  CALL Splot(5, a,b)
  WRITE(*,*) "Terminated by EndFil"
  STOP
END Subroutine Endfil   ! ---------------------------------------------------



!+
SUBROUTINE ErrorMessage(errorCode)
! ---------------------------------------------------------------------------
! PURPOSE - Print error message
!
USE Blank
  IMPLICIT NONE
  INTEGER,INTENT(IN):: errorCode
!!!  INCLUDE 'blank.cmn'
!----------------------------------------------------------------------------
  WRITE(6,*) "Error Code ", errorCode
  last=1
  RETURN
END Subroutine ErrorMessage   ! ---------------------------------------------

!+
SUBROUTINE Flint()
! ---------------------------------------------------------------------------
! PURPOSE - Compute the point of intersection of the flow field with the
!   cowl lip
!
! NOTES - Called from main program
USE Blank
!!!  INCLUDE 'blank.cmn'

  REAL(DP):: da,db
  REAL(DP):: den
  INTEGER:: ichk
  INTEGER:: jq,jm,jn,kq,km,kn
  INTEGER:: L                ! maybe get rid of this
  REAL(DP):: ra,rb
  REAL(DP):: rata,ratb,ratc
  REAL(DP):: s1,s2,s3
  REAL(DP):: sa,sb
  REAL(DP):: t1
  REAL(DP):: wa,wb
  REAL(DP):: xa,xb
!----------------------------------------------------------------------------
write(DBG,*) "Entering Flint"  

! see if shock wave has fallen inside the cowl lip ....
  IF (X(I,J,K) .GE. ATAB(1,1).AND. R(I,J,K) .LT. ATAB(2,1)) THEN
    CALL ErrorMessage(12)
    RETURN
  END IF

! compute the point of intersection of the cowl and the flow
! field, using the last two rays computed ....

 6 L=2
29 JM=J
   KM=K
   JN=J
   KN=K-1
   JQ=JP
   KQ=KP+i

 7 IF (KN <= 0) RETURN
 8 CONTINUE
!!!    26 CALL DVCHK(ICHK)
   S1=(R(I,JQ,KQ)-R(I,JM,KM))/(X(I,JQ,KQ)-X(I,JM,KM))
   S2=(R(I,JM,KM)-R(I,JN,KN))/(X(I,JM,KM)-X(I,JN,KN))
   S3=(R(I,JQ,KQ)-R(I,JN,KN))/(X(I,JQ,KQ)-X(I,JN,KN))
!!!    CALL DVCHK(ICHK)
   ichk=2
   GO TO (14,10),ICHK
10 T1=ATAB(2,1)-R(I,JM,KM)-S3*ATAB(1,1)
   XA=(T1+S1*X(I,JM,KM))/(S1-S3)
   XB=(T1+S2*X(I,JM,KM))/(S2-S3)
   IF (XA-ATAB(1,1)) 12,12,13
13 IF (XB-ATAB(1,1)) 15,15,14
12 IF (XB-ATAB(1,1)) 14,15,15
14 GO TO (16,17),L
16 JN=J
   KQ=KN
   KN=KM-1
   IF (R(I,JM,KM) .LT. ATAB(2,1)) RETURN
   L=2
   IF (KN <= 0) THEN
     RETURN
   ELSE
     GO TO 8
   END IF

17 JN=JP
   KM=KN
   KN=KQ-i
   IF (R(I,JQ,KQ) .LT. ATAB(2,1)) RETURN
   L=1
   GO TO 7

15 RA=R(I,JM,KM)+S1*(XA-X(I,JM,KM))
   IF (RA-R(I,JM,KM)) 14,28,28
28 RB=R(I,JM,KM)+S2*(XB-X(I,JM,KM))
   RATA=(XA-X(I,JM,KM))/(X(I,JQ,KQ)-X(I,JM,KM))
   RATB=(XB-X(I,JM,KM))/(X(I,JN,KN)-X(I,JM,KM))
   DA=DEL(I,JM,KM)+(DEL(I,JQ,KQ)-DEL(I,JM,KM))*RATA
   DB=DEL(I,JM,KN)+(DEL(I,JN,KN)-DEL(I,JM,KM))*RATB
   WA=W(I,JM,KM)+(W(I,JQ,KQ)-w(I,JM,KM))*RATA
   WB=W(I,JM,KM)+(W(I,JN,KN)-W(I,JM,KM))*RATB
   SA=S(I,JM,KM)+(S(I,JQ,KQ)-S(I,JM,KM))*RATA
   SB=S(I,JM,KM)+(S(I,JN,KN)-S(I,JM,KM))*RATB
   DEN=XA-XB
   IF (ABS(DEN) < 1.E-6) THEN
     ratc=0.0
     k=km
     write(DBG,*) "k set to km in Flint. Now=", k
     GO TO 22
   END IF

   RATC=(ATAB(1,1)-XB)/DEN
   GO TO (21,20),L
20 K=KM
   GO TO 22
21 J=JQ
   write(DBG,*) "In Flint, J has been set to value of JQ. Now=", j
   K=KQ
   write(DBG,*) "k set to kq in Flint. Now=", k
   IRAY=IRAY-1
   write(DBG,*) "iray decremented in Flint. Now it is ", iray
   JP=J-1
   IF (JP .LE. 0.0) JP=4
22 X(I,J,K)=ATAB(1,1)
   R(I,J,K)=ATAB(2,1)
   DEL(I,J,K)=DB+(DA-DB)*RATC
   W(I,J,K)=WB+(WA-WB)*RATC
   S(I,J,K)=SB+(SA-SB)*RATC
   CALL PUNT(1)
   IF (last > 0) RETURN
23 NOP(I,J)=K
   J=J
   GO TO (24,25,24,25),J
24 IN=K
   GO TO 5
25 IN=K+1
 5 ITYPE=2
   write(DBG,*) "ITYPE set to 2 in Flint"
   WRITE(DBG,*) "Leaving Flint"
   RETURN


!!!18 RATC=0.0
!!!   K=KM
!!!   write(DBG,*) "k set to km in Flint(18). Now=", k
!!!   GO TO 22
!!! 4 CALL ErrorMessage(12)
!!! 1 RETURN

END Subroutine Flint     ! -------------------------------------------------------

!+
SUBROUTINE Flow()
! ---------------------------------------------------------------------------
! PURPOSE - Flow field point
!
! NOTES - Called from main program and UpSc
USE Blank
!!!  INCLUDE 'blank.cmn'
  INTEGER:: idim
  COMMON /DIM/IDIM

  REAL(DP):: a,b  ! where does this come from????
  REAL(DP):: a1,a2
  REAL(DP):: brak
  REAL(DP):: c1,c2
  REAL(DP):: cor1,cor2
  REAL(DP):: d1,d2
  REAL(DP):: delt,deltt
  REAL(DP):: dprev
  INTEGER:: icow
  INTEGER:: iter
  REAL(DP):: ra1,ra2
  REAL(DP):: t,t1,t2     ! CHECK THIS
  REAL(DP):: tana1,tana2

!----------------------------------------------------------------------------
write(DBG,*) "Entering Flow"
  DO 30 ITER=1,25                     ! big loop; almost the whole subroutine
    WRITE(DBG,*) "Iteration ",iter
1    SELECT CASE(IFAM)
      CASE(1)
        t=1.0
      CASE(2)
        t=-1.0
    END SELECT

    A1=U(I,JP,KP)+DEL(I,JP,KP)*T
    A2=U(I,JP,KP+1)-DEL(I,JP,KP+1)*T
    TANA1=TAN(A1)
    TANA2=TAN(A2)
    T1=X(I,JP,KP)*TANA1+X(I,JP,KP+1)*TANA2
    T2=TANA1+TANA2
    X(I,J,K)=(R(I,JP,KP+1)-R(I,JP,KP)+ T1*T)/(T2*T)
    T1=(X(I,J,K)-X(I,JP,KP))*TANA1
    R(I,J,K)=R(I,JP,KP)+ T1*T
    C2=0.0
    COR2=CRFUN(R(I,J,K), R(I,JP,KP+1), A2)
    GO TO (26,26,25),IDIM
 25 C2=CFUN(COR2,U(I,JP,KP+1),DEL(I,JP,KP+1))
 26 RA1=RAFUN(W(I,JP,KP),U(I,JP,KP))
    RA2=RAFUN(W(I,JP,KP+1),U(I,JP,KP+1))
    D1=DFUN(U(I,JP,KP))         ! only occurence of Dfun
    D2=DFUN(U(I,JP,KP+1))       !   ditto   (maybe add gamma)
    IF (R(I,JP,KP)) 8,8,9
  8 DEL(I,J,K)= &
       (DEL(I,JP,KP+1)*RA2+W(I,JP,KP+1)-W(I,JP,KP)+C2*RA2)/(2.0*RA1+RA2)
     C1=0.0
     COR1=0.0
     GO TO 3

   9 C1=0.0
  29 COR1=CRFUN(R(I,J,K),R(I,JP,KP),A1)
     GO TO (28,28,27),IDIM
  27 C1=CFUN(COR1,U(I,JP,KP),DEL(I,JP,KP))
  28 T1=W(I,JP,KP+1)-W(I,JP,KP)-C1*RA1+C2*RA2
     DEL(I,J,K)=(DEL(I,JP,KP)*RA1+RA2*DEL(I,JP,KP+1)+ T1*T)/(RA1+RA2)
   3 DELT=DEL(I,J,K)
     DO 33 ICOW=1,25
       DELTT=DEL(I,J,K)
       A=COR1*R(I,JP,KP)*SIN(A1-DEL(I,J,K)*T )
       B=COR2*R(I,JP,KP+1)-SIN(A2+DEL(I,J,K)*T )
       S(I,J,K)=S(I,JP,KP)+(S(I,JP,KP+1)-S(I,JP,KP))*A/(A+B)
       BRAK=D1*RA1*(S(i,j,k)-S(i,JP,KP))-D2*RA2*(s(i,j,k)-s(i,jp,kp+1))
       BRAK=BRAK/(RA1+RA2)
       DEL(I,J,K)=DELT+BRAK*T
       IF (ABS(DEL(I,J,K)-DELTT)-TEST) 10,10,33
  33 END DO
     WRITE(DBG,*) "Completed loop 33 without branching to 10"
     CALL ErrorMessage(5)
     RETURN


  10 T1=RA2*(DEL(I,J,K)-DEL(I,JP,KP+1))
     W(I,J,K)= -T1*T +W(I,JP,KP+1)+C2*RA2-D2*RA2*(S(I,J,K)-S(I,JP,KP+1))
     IF (ITER-1) 11,11,12
  12 IF (ABS(DEL(I,J,k)-DPREV)-TEST) 13,13,2
  13 CALL JUGGLE(9)
  14 IF (X(I,J,K)-X(I,JP,KP+1)) 20,20,22
  22 IF (ABS(X(I,J,K)-X(I,JP,KP+1))/XT-COALT) 23,21,21
  23 IF (ABS(R(I,J,K)-R(I,JP,KP+1))/XT-COALT) 20,21,21
  20 CALL PUNT(2)
     GO TO 15
  21 CALL PUNT(1)
  15 RETURN                ! The Success way out
  11 IF (COR2-CRMAX) 17,17,18
  17 IF (R(I,JP,KP) <= 0.0) GO TO 14
  19 IF (COR1 <= CRMAX) GO TO 14
  18 CALL JUGGLE(3)
   2 DPREV=DEL(I,J,K)
     CALL JUGGLE(6)
30 END DO
  WRITE(DBG,*) "Completed big loop (30) without taking a return path"
  CALL ErrorMessage(5)   ! unable to converge

  RETURN
END Subroutine Flow   ! -----------------------------------------------------

!+
SUBROUTINE Juggle(kArgument)
! ---------------------------------------------------------------------------
! PURPOSE - Refines the soultions when the mesh size is large by
!   averaging upstream points
!
USE Blank
  IMPLICIT NONE

  INTEGER,INTENT(IN):: kArgument    ! can be 1..9
!!!  INCLUDE 'blank.cmn'
  REAL(DP),SAVE,DIMENSION(12):: t
!!    DIMENSION AA(1),T(12)

  INTEGER:: kpp1
!----------------------------------------------------------------------------
write(DBG,*) "Entering Juggle, kArgument=", kArgument

  KPP1=KP+1

  SELECT CASE(kArgument)
    CASE(1)
      t(1)=del(i,jp,kp)
      t(2)=w(i,jp,kp)
      t(3)=s(i,jp,kp)
      t(4)=u(i,jp,kp)
      t(5)=x(i,jp,kp)
      t(6)=r(i,jp,kp)

    CASE(2)
      t(7)=del(i,jp,kpp1)
      t(8)=w(i,jp,kpp1)
      t(9)=s(i,jp,kpp1)
      t(10)=u(i,jp,kpp1)
      t(11)=x(i,jp,kpp1)
      t(12)=r(i,jp,kpp1)

    CASE(3)
      t(1)=del(i,jp,kp)
      t(2)=w(i,jp,kp)
      t(3)=s(i,jp,kp)
      t(4)=u(i,jp,kp)
      t(5)=x(i,jp,kp)
      t(6)=r(i,jp,kp)
      t(7)=del(i,jp,kpp1)
      t(8)=w(i,jp,kpp1)
      t(9)=s(i,jp,kpp1)
      t(10)=u(i,jp,kpp1)
      t(11)=x(i,jp,kpp1)
      t(12)=r(i,jp,kpp1)


    CASE(4)
      del(i,jp,kp)=0.5*(del(i,j,k)+del(i,jp,kp))
      w(i,jp,kp)=0.5*(w(i,j,k)+w(i,jp,kp))
      s(i,jp,kp)=0.5*(s(i,j,k)+s(i,jp,kp))
      u(i,jp,kp)=ufun(w(i,jp,kp))
      x(i,jp,kp)=0.5*(x(i,jp,kp)+x(i,j,k))
      r(i,jp,kp)=0.5*(r(i,jp,kp)+r(i,j,k))

    CASE(5)
      x(i,jp,kpp1)=0.5*(x(i,jp,kpp1)+x(i,j,k))
      r(i,jp,kpp1)=0.5*(r(i,jp,kpp1)+r(i,j,k))
      del(i,jp,kpp1)=0.5*(del(i,jp,kpp1)+del(i,j,k))
      w(i,jp,kpp1)=0.5*(w(i,jp,kpp1)+w(i,j,k))
      s(i,jp,kpp1)=0.5*(s(i,jp,kpp1)+s(i,j,k))
      u(i,jp,kpp1)=ufun(w(i,jp,kpp1))


    CASE(6)
      del(i,jp,kp)=0.5*(del(i,j,k)+del(i,jp,kp))
      w(i,jp,kp)=0.5*(w(i,j,k)+w(i,jp,kp))
      s(i,jp,kp)=0.5*(s(i,j,k)+s(i,jp,kp))
      u(i,jp,kp)=ufun(w(i,jp,kp))
      x(i,jp,kp)=0.5*(x(i,jp,kp)+x(i,j,k))
      r(i,jp,kp)=0.5*(r(i,jp,kp)+r(i,j,k))

      x(i,jp,kpp1)=0.5*(x(i,jp,kpp1)+x(i,j,k))
      r(i,jp,kpp1)=0.5*(r(i,jp,kpp1)+r(i,j,k))
      del(i,jp,kpp1)=0.5*(del(i,jp,kpp1)+del(i,j,k))
      w(i,jp,kpp1)=0.5*(w(i,jp,kpp1)+w(i,j,k))
      s(i,jp,kpp1)=0.5*(s(i,jp,kpp1)+s(i,j,k))
      u(i,jp,kpp1)=ufun(w(i,jp,kpp1))


    CASE(7)
      del(i,jp,kp)=t(1)
      w(i,jp,kp)=t(2)
      s(i,jp,kp)=t(3)
      u(i,jp,kp)=t(4)
      x(i,jp,kp)=t(5)
      r(i,jp,kp)=t(6)

    CASE(8)
      r(i,jp,kpp1)=t(12)
      x(i,jp,kpp1)=t(11)
      del(i,jp,kpp1)=t(7)
      w(i,jp,kpp1)=t(8)
      s(i,jp,kpp1)=t(9)
      u(i,jp,kpp1)=t(10)

    CASE(9)
      del(i,jp,kp)=t(1)
      w(i,jp,kp)=t(2)
      s(i,jp,kp)=t(3)
      u(i,jp,kp)=t(4)
      x(i,jp,kp)=t(5)
      r(i,jp,kp)=t(6)

      r(i,jp,kpp1)=t(12)
      x(i,jp,kpp1)=t(11)
      del(i,jp,kpp1)=t(7)
      w(i,jp,kpp1)=t(8)
      s(i,jp,kpp1)=t(9)
      u(i,jp,kpp1)=t(10)

  END SELECT
  WRITE(DBG,*) "Leaving Juggle"
  RETURN
END Subroutine Juggle   ! -------------------------------------------------------


!+
SUBROUTINE Punt(kArgument)
! ---------------------------------------------------------------------------
! PURPOSE - input/output
!
USE Blank
  INTEGER,INTENT(IN):: kArgument
!!!  INCLUDE 'blank.cmn'

  CHARACTER(LEN=*),PARAMETER:: string1 =  &
    "TWO-DIMENSIDNAL METHOD OF CHARACTERISTICS. INTERNAL CASE"
  CHARACTER(LEN=*),PARAMETER:: string2 =  &
    "THREE-DIMENSIONAL AXISYMMETRIC METHOD OF CHARACTERISTICS. INTERNAL CASE"
  CHARACTER(LEN=*),PARAMETER:: string3 =  &
    "LIP INTERSECTION  SL="
  CHARACTER(LEN=*),PARAMETER:: string4 =  &
    "   RHO/RHO L="
  CHARACTER(LEN=*),PARAMETER:: string5 =  &
    " REG RAY POINT     X          R       P/PINF   DELTA(DEG)  MACH NO.   PT/PTINF"
  CHARACTER(LEN=*),PARAMETER:: string6 =  "COALESCENCE"
!!  CHARACTER(LEN=*),PARAMETER:: string7 =  &
!!    "END OF BODY HAS BEEN REACHED. CASE TERMINATED."
!!  CHARACTER(LEN=*),PARAMETER:: FMT11 =  "(2F8.4)"
  CHARACTER(LEN=*),PARAMETER:: FMT100 = "(3I4,6F11.6)"

  REAL(DP):: delta
  REAL(DP):: em
  INTEGER:: ibod
  INTEGER:: idim  ! where does this come from????????????
  INTEGER,SAVE:: line
  REAL(DP):: p1,p2,p3
  CHARACTER(LEN=80):: sbhed
  REAL(DP):: rhol
  REAL(DP):: sl
  REAL(DP):: ta,tb
!----------------------------------------------------------------------------
write(DBG,'(A,I3)') "Entering Punt, argumemt=", kArgument

!  SELECT CASE(kArgument)
!    CASE(1)
!    CASE(2)
!    CASE(3)
!    CASE(4)
!    CASE(5)
!    CASE(6)
!    CASE(7)
!    CASE(8)
!    CASE(9)
!    CASE(10)
!  END SELECT


   GO TO (1,2,3,4,5,4,4,10,16,27),kArgument

16 IBOD=2
   GO TO 11

10 IBOD=1
   GO TO 11

 1 IBOD=3
11 TA=1.0-0.5*(GAMMA-1.0)*W(I,J,K)**2
   IF (TA <= 0.0) THEN
     WRITE(DBG,*) "Non-positive TA in PUNT"
     CALL ErrorMessage(6)
     RETURN
   END IF

   TB=SQRT(TA)/W(I,J,K)
   IF (TB > 1.0) THEN
     WRITE(DBG,*) "TB > 1 in PUNT"
     CALL ErrorMessage(6)
     RETURN
   END IF

22 U(I,J,K)=ASIN(TB)    ! Eq 9
   EM=1.0/TB
   DELTA=DEL(I,J,K)*57.2957795
   P1=EXP(SING-S(I,J,K))         ! Eq 10

12 P2=TA**(GAMMA/(GAMMA-1.0))           ! Eq 11
   P3=P1*P2*P4                           ! Eq 12
   WRITE(6,FMT100)IREG,IRAY,K,X(I,J,K),R(I,J,K),P3,DELTA, EM,P1
   WRITE(DBG,FMT100)IREG,IRAY,K,X(I,J,K),R(I,J,K),P3,DELTA, EM,P1
   GO TO (17,18,19),IBOD

17 CALL SPLOT(6,X(I,J,K),EM)
   CALL SPLOT(7,X(I,J,K),P3)
   GO TO 19

18 CALL SPLOT( 8,X(I,J,K),EM)
   CALL SPLOT( 9,X(I,J,K),P3)

19 CALL SPLOT( 3,X(I,J,K),R(I,J,K))
!!!   IF (P1- 1.0) 9,9,24
   IF (p1 <= 1.0) GO TO 9

24 IF (P1 > 1.0+TEST) THEN
     WRITE(*,*) "Total pressure ratio greater than 1"
     CALL ErrorMessage(7)
     RETURN
   END IF
   P1=1.0   ! just in case it is 1+eps

 9 LINE=LINE+1
   IF (LINE > 600) THEN
!!    CALL PAGE       ! write general header, local title, column headers
     WRITE(6,*) Trim(generalTitle)
     WRITE(6,*) string5
     LINE=1
   END IF
  RETURN

 2 WRITE(6,'(3I4,2F11.6,24X,A)') IREG,IRAY,K,X(I,J,K),R(I,J,K),string6
   WRITE(DBG,'(3I4,2F11.6,24X,A)') IREG,IRAY,K,X(I,J,K),R(I,J,K),string6


   IFAM=-IFAM
   GO TO 9

 3 WRITE (6,*) "End of body has been reached. Case Terminated!"
   LAST=1
   RETURN

 4 SELECT CASE(IDIM)     !!! says idim used but never set???
    CASE(2)
      WRITE(6,*) string1
    CASE(1,3)
      WRITE(6,*) string2
  END SELECT
  WRITE(6,*) Trim(generalTitle)
  WRITE(6,*) string5
  RETURN


5  READ(5,'(A)') sbhed
  IF (sbhed(1:4) == "DONE") CALL ENDFIL() 
!!!!  CALL SPLOT(2,SBHED,B)
  RETURN

 27 SL= SING + LOG(1.0/P1)
    RHOL= (P3*EXP((1.0-GAMMA)*(SING-SL)))**(1.0/GAMMA)
    SL= 1716.0*SL

  WRITE(6,'(A,ES15.7)') string3, sL
  WRITE(6,'(A,ES15.7)') string4, rhoL
  LAST=1
 
  RETURN
END Subroutine Punt   ! -----------------------------------------------------

!+
SUBROUTINE Shock(dup)
! ---------------------------------------------------------------------------
! PURPOSE - Compute a shock point
!
USE Blank
  REAL(DP),INTENT(IN OUT):: dup    ! is this really IN OUT ?????

!!!  EXTERNAL Abody,Cbody

  INTEGER:: idim
  COMMON /DIM/IDIM
!!!  INCLUDE 'blank.cmn'

  REAL(DP):: a1,a2
  REAL(DP):: c1
  REAL(DP),DIMENSION(4):: co
  REAL(DP):: cor1       !  c/r dimensionless incremental distance along a characteristic
  REAL(DP):: d1
  REAL(DP):: delta
  REAL(DP):: dold
  REAL(DP):: dupre
  REAL(DP):: emup
  REAL(DP):: g1,g2,g3,g4,g5
  INTEGER:: it
  INTEGER:: jm, km
  REAL(DP):: ra1
  REAL(DP):: rb
  REAL(DP):: rint
  REAL(DP):: rl
  REAL(DP):: root
  REAL(DP):: sds
  REAL(DP):: sj,sk
  REAL(DP):: slob
  REAL(DP):: sup
  REAL(DP):: t              ! makes the compatibility eqns have right sign
  REAL(DP):: t1,t2,t3
  REAL(DP):: tana1,tana2
  REAL(DP):: tp
  REAL(DP):: wup
  REAL(DP):: xb
  REAL(DP):: xint
  REAL(DP):: z
!----------------------------------------------------------------------------
  WRITE(DBG,*) "Entering Shock,  IFAM=", ifam

    TP=theta       ! save previous shock angle
    DUPRE=DUP
    JM=JP
    KP=KP-1
    KM=KP+1

    IF (ifam == 1) THEN
      t=1.0
    ELSE
      t=-1.0
    END IF

  a2=tp+dupre*t
  a1=u(i,j,k-1)+del(i,j,k-1)*t
  tana1=tan(a1)
  tana2=tan(a2)
5 t1=x(i,j,k-1)*tana1-x(i,jm,km)*tana2
  t2=tana1-tana2
  x(i,j,k)=(r(i,jm,km)-r(i,j,k-1)+t1*t)/(t2*t)
6 t3=(x(i,j,k)-x(i,j,k-1))*tana1
  r(i,j,k)=r(i,j,k-1)+ t3*t
  CALL Upsc(dup,wup,sup,emup,xb,rb)
  IF (last > 0) RETURN
  IF (ABS(T2) .LE. COALT) GO TO 62
  IF (X(I,J,K) .GT. X(I,JP,KP+1)) GO TO 9

62 IF (IREG .LE. 1) GO TO 9
  x(i,j,k)=xb     ! the first region
  r(i,j,k)=rb
  s(i,j,k)=sup
  w(i,j,k)=wup
  del(i,j,k)=dup
  CALL Punt(1)
  RETURN

9 G1=EMUP**2
  G2=G1**2
  G3=(G1+2.0)/G1
  G4=(2.0*G1+1.0)/G2
  G5=(GAMMA+1.0)**2/4.0+(GAMMA-1.0)/G1
  WRITE(DBG,'(A,6ES12.3)' ) "In Shock, emup...=", emup,g1,g2,g3,g4,g5
  WRITE(DBG,*) "In Shock, itype=", itype
  CALL JUGGLE(1)
  IF (IREG > 1) GO TO 77

21 IF (IRAY > 2) GO TO 23
10 IF (SPACE .LE. 0.0) SPACE=0.5
24 SPACE= X(I,JM,KM) *SPACE   ! set spacing on shock wave to half initial x

23 XINT=X(I,JM,KM)+SPACE
   RINT=R(I,JM,KM)+SPACE*TAN(TP)
   IF (XINT .GE. X(I,J,K-1)) GO TO 20
   SPACE=2.0*SPACE
   GO TO 23

77 IF (ITYPE == 2) GO TO 78
27 XINT=XB
   RINT=RB
   GO TO 20
78 XB=X(I,JM,KM)
   RB=R(I,JM,KM)
   SLOB= T*TANA2

   IF (IFAM <= 1) THEN
 4   CALL BSINT(ABODY,ATAB(:,:),NOA,XB,RB,SLOB,XINT,RINT)
   ELSE
11   CALL BSINT(CBODY,CTAB(:,:),NOB,XB,RB,SLOB,XINT,RINT)
   END IF

20 X(I,J,K)=XINT
   R(I,J,K)=RINT
   SK=(R(i,J,K-1)-R(I,J ,K ))/(X(I,J,K-1)-X(I,J ,K ))
   SJ=(R(I,J,K-1)-R(I,JP,KM))/(X(I,J,K-1)-X(I,JP,KM))
   X(I,JP,KP)=(SK*XINT-SJ*X(I,J,K-1)-RINT+R(I,J,K-1))/(SK-SJ)
   R(I,JP,KP)=RINT+(X(I,JP,KP)-XINT)*SK
   RL=(X(I,JP,KP)-X(I,JP,KM))/(X(I,J,K-1)-X(I,JP,KM))
   DEL(I,JP,KP)=DEL(I,JP,KM)+RL*(DEL(I,J,K-1)-DEL(I,JP,KM))
   W(I,JP,KP)=    W(I,JP,KM)+RL*(  W(I,J,K-1)-  W(I,JP,KM))
   S(I,JP,KP)=    S(I,JP,KM)+RL*(  S(I,J,K-1)-  S(I,JP,KM))
   U(I,JP,KP)=    U(I,JP,KM)+RL*(  U(I,J,K-1)-  U(I,JP,KM))

   IF (IDIM == 2) THEN
 3   COR1=0.0                                         ! two-D
     C1=0.0
   ELSE    
 7   COR1=(R(I,J,K)-R(I,JP,KP))/R(I,JP,KP)/SIN(A1)    ! axisymetric
     COR1=ABS(COR1)
     C1=COR1*SIN(U(I,JP,KP))*SIN(DEL(I,JP,KP))
   END IF

25 RA1=W(I,JP,KP)*TAN(U(I,JP,KP))
   D1=0.5*SIN(2.0*U(I,JP,KP))/GAMMA
 8 DEL(I,J,K)=DEL(I,JP,KP)-C1*T

   DO 99 IT=1,50
     DELTA=DUP-DEL(I,J,K)
     SDS=SIN(DELTA)**2
     CO(4)=1.0
     CO(3)=-G3-GAMMA*SDS
     CO(1)=(SDS-1.0)/G2
     CO(2)=G4+G5*SDS
     CALL CUBIC(co(:),Z)    ! returns z=sin(theta)**2
     WRITE(DBG,*) "In Shock, iterating for Z", it,z,delta
12   T1=(2.0*GAMMA*G1*Z-GAMMA+1.0)/(GAMMA+1.0)
     IF (T1 <= 0.0) THEN
       WRITE(DBG,*) "Non-positive t1 in Shock", t1,g1,z
       CALL ErrorMessage(8)
       RETURN
     END IF
     T2=((GAMMA+1.0)*G1*Z)/((GAMMA-1.0)*G1*Z+2.0)
     IF (T2 <= 0.0) THEN
       WRITE(DBG,*) "Non-positive t2 in Shock", t1,g1,z
       CALL ErrorMessage(8)
       RETURN
     END IF
     S(i,J,K)=SUP+(LOG(T1)-GAMMA*LOG(T2))/(GAMMA-1.0)
        ! could write the following line better
     T1=1.0-4.0*(G1*Z-1.0)/(GAMMA+1.0)**2*(GAMMA*G1*Z+1.0)/(Z*G2)
     IF (T1 < 0.0) THEN
       WRITE(DBG,*) "Negative t1 in Shock:", t1
       WRITE(DBG,*) "gamma,g1,g2,z", gamma,g1,g2,z
       CALL ErrorMessage(9)
       RETURN
     END IF
     W(I,J,K)=WUP*SQRT(T1)                               ! Eq16
     DOLD=DEL(I,J,K)
     T1=(W(I,J,K)-W(I,JP,KP))/RA1-C1+D1*(S(I,J,K)-S(I,JP,KP))
     DEL(I,J,K)=DEL(I,JP,KP)+T1*T                        ! Eq17
  31 IF (ABS(DEL(I,J,K)-DOLD) .LE. TEST) GO TO 19
     DEL(I,J,K)=0.5*(DEL(I,J,K)+DOLD)
99 END DO    ! end of big loop

19 ROOT=SQRT(Z)
   IF (ROOT > 1.0) THEN
     CALL ErrorMessage(10)
     RETURN
   END IF

   THETA=ASIN(ROOT)
   CALL JUGGLE(7)
22 CALL PUNT(1)
   WRITE(DBG,*) "Leaving Shock at 80 return"
80 RETURN
END Subroutine Shock   ! -------------------------------------------------------


!+
SUBROUTINE Splot(k,x,y)
! ---------------------------------------------------------------------------
! PURPOSE - Dummy subroutine for splot
  INTEGER,INTENT(IN):: k
  REAL(DP),INTENT(IN):: x,y
!
!----------------------------------------------------------------------------
  WRITE(FIG,*) k,x,y
  RETURN
END Subroutine Splot   ! -------------------------------------------------------


!+
SUBROUTINE UpSc(db,wb,sb,emup,xb,rb)
! ---------------------------------------------------------------------------
! PURPOSE - Compute the upstream conditions for a shock point
!
! NOTES - Called only from Shock
USE Blank

  REAL(DP),INTENT(OUT):: db
  REAL(DP),INTENT(OUT):: wb
  REAL(DP),INTENT(OUT):: sb
  REAL(DP),INTENT(OUT):: emup
  REAL(DP),INTENT(OUT):: xb
  REAL(DP),INTENT(OUT):: rb

!!!  INCLUDE 'blank.cmn'

  REAL(DP):: el2,em2,em3          ! BOTH el2 and em2  ???
  INTEGER:: ip
  INTEGER:: is,jm,jn,km,kq,kk
  INTEGER:: iswt
  INTEGER:: loopVar
  REAL(DP):: rc
  REAL(DP):: sl
  REAL(DP):: t1
  REAL(DP):: ta
  REAL(DP):: xc
  REAL(DP):: xprev

!----------------------------------------------------------------------------
write(DBG,*) "Entering UpSc"

  IF (ireg < 1) THEN
    CALL ErrorMessage(16)
    RETURN
  END IF

  IF (ireg ==1) THEN
    DB=0.0
    WB=WIN
    SB=SING
    EMUP=EMIN
    RETURN
  END IF

   XC=X(I,J,K)
   RC=R(I,J,K)
   JM=JP
   KM=KP+1
   XPREV=X(I,JM,KM)
 2 SL=(RC-R(I,JM,KM))/(XC-X(I,JM,KM))
   ASSIGN 5 TO ISWT
   GO TO 50
 5 IRAY=IRAY+1
   WRITE(DBG,*) "IRAY incremented in UpSc. Now ", iray
   IF (IN < 2) THEN
     CALL ErrorMessage(16)
     RETURN
   END IF
   IF (IN > 2) GO TO 71
!!!    IF (IN-2) 67,13,71
13 J=J

!!!    GO TO (67,16,67,16),J
  IF (j==1 .OR. j==3) THEN
    CALL ErrorMessage(16)
    RETURN
  END IF

16 IS=0
   GO TO 68

71 J=J+1
   write(DBG,*) "J incremented in UpSc. Now=", j
   JP=JP+1
   K=1
   write(DBG,*) "k set to 1 in UpSc"
   KP=0
61 GO TO (56,56,57,70,59),J
56 JP=1
70 IN=IN-1
69 KP=KP+1
   GO TO 65
59 J=1
   write(DBG,*) "J set to 1 in UpSc"
57 IF (IFAM-1) 62,62,63
62 CALL BODY(CBODY, ctab(:,:), NOB)
   GO TO 64
63 CALL BODY(ABODY, atab(:,:), NOA)
64 K=K+1
   write(DBG,*) "k incremented in UpSC. Now=", k
   KP=KP+1
   IF (LAST) 11,11,501
11 IF (K-IN+1) 65,65,66
65 CALL FLOW
   IF (IFAM) 1,1,64
 1 X(I,J,K)=X(I,JP,KP+1)
   R(I,J,K)=R(I,JP,KP+1)
   W(I,J,K)=W(I,JP,KP+1)
   S(I,J,K)=S(I,JP,KP+1)
   U(I,J,K)=U(I,JP,KP+1)
   DEL(I,J,K)=DEL(I,JP,KP+1)
   K=K+1
   write(DBG,*) "k incremented in UpSC (before 3). Now=", k
   KP=KP+1
   IF (KP-NOP(I,JP)) 1,3,3
 3 IFAM=-IFAM
   NOP(I,J)= K-1
   IF (LAST) 5,5,501
66 NOP(I,J)=IN-1
 4 I=I                          ! curious!! stuff like this used to be done
   J=J
   K=NOP(I,J)
   write(DBG,*) "k set to nop(i,j) in UpSC. Now=", k
 6 KP=K-1
   GO TO (8,7,8,7),J
 7 KP=K
 8 JN=JP
   IS=1
   KQ=KP+1             ! kq never used ???????
   KK=KP
 9 EM3=SL
12 EM2=(R(I,JN,KK)-R(I,J,K))/(X(I,JN,KK)-X(I,J,K))
15 T1=RC-R(I,J,K)-EM3*XC
   XB=(T1+EM2*X(I,J,K))/(EM2-EM3)
   IF(XB-X(I,JN,KK)) 18,18,19
18 IF (IN-2) 16,16,20
20 J=J
   JP=JP-1
   GO TO (22,27,26,21),J
22 j=5
   write(DBG,*) "J set to 5 in UpSc"
26 IN=IN-1
   GO TO 21
27 JP=4
21 J=J-1
   write(DBG,*) "J decremented in UpSc. Now=", j
23 NOP(i,J)=NOP(i,J)-1
   IRAY=IRAY-1
   write(DBG,*) "IRAY decremented in UpSc. Now=", iray
   GO TO 4

19 IF (XB- XPREV - COALT)    5,5,17
17 CONTINUE
14 RB=R(I,J,K)+EM2*(XB-X(I,J,K))
   EL2=(XB-X(I,J,K))/(X(I,JN,KK)-X(I,J,K))
   DB=DEL(I,J,K)+EL2*(DEL(I,JN,KK)-DEL(I,J,K))
   WB=W(I,J,K)+EL2*(W(I,JN,KK)-W(I,J,K))
   SB=S(I,J,K)+EL2*(S(I,JN,KK)-S(I,J,K))
   TA=1.0-0.5*(GAMMA-1.0)*WB**2
   IF (TA) 44,44,45
45 EMUP= WB/SQRT(TA)
68 ASSIGN 48 TO ISWT
   GO TO 50

48 CONTINUE
47 IF (IS)  500,500,501
500 ITYPE=2
    write(DBG,*) "ITYPE set to 1 in UpSc"
501 RETURN

50 GO TO (51,52),I

51 IP=1
   GO TO 53
52 I=1
   write(DBG,*) "I set to 1 in UpSc"
   IP=2
53 DO 54 loopVar=1,9
     ICON(IP,loopVar)=IRR(loopVar)
     IRR(loopVar)=ICON(I,loopVar)
54 END DO
   write(DBG,*) "col ", IP, " of ICON replaced with irr"
   write(DBG,*) "irr replaced with col ", I, " of icon"

   GO TO ISWT,(5,48)
44 CALL ErrorMessage(17)
  RETURN
END Subroutine UpSc  ! -------------------------------------------------------


!+
FUNCTION CrFun(a,b,c) RESULT(t)
! ---------------------------------------------------------------------------
  REAL(DP),INTENT(IN):: a,b,c
  REAL(DP):: t
!----------------------------------------------------------------------------
  t=ABS((b-a)/(b*SIN(c)))
  RETURN
END Function CrFun   ! ------------------------------------------------------

!+
FUNCTION CFun(a,b,c) RESULT(t)
! ---------------------------------------------------------------------------
  REAL(DP),INTENT(IN):: a,b,c
  REAL(DP):: t
!----------------------------------------------------------------------------
  t=a*SIN(b)*SIN(c)
  RETURN
END Function CFun   ! -------------------------------------------------------

!+
FUNCTION RaFun(a,b) RESULT(t)
! ---------------------------------------------------------------------------
  REAL(DP),INTENT(IN):: a,b
  REAL(DP):: t
!----------------------------------------------------------------------------
  t=a*TAN(b)
  RETURN
END Function RaFun   ! ------------------------------------------------------

!+
FUNCTION DFun(a) RESULT(t)
! ---------------------------------------------------------------------------
! called from Flow
USE Blank,ONLY: GAMMA
  REAL(DP),INTENT(IN):: a
  REAL(DP):: t
!----------------------------------------------------------------------------
  t=SIN(a+a)/GAMMA   ! gamma is global because /blank/ is in main
  RETURN
END Function DFun   ! ------------------------------------------------------

!+
FUNCTION UFun(a) RESULT(t)
! ---------------------------------------------------------------------------
! called from Juggle
USE Blank,ONLY: GAMMA
  REAL(DP),INTENT(IN):: a
  REAL(DP):: t
!----------------------------------------------------------------------------
  t=ASIN(SQRT(1.0-0.5*(GAMMA-1.0)*a*a)/a)
  RETURN
END Function UFun   ! -------------------------------------------------------




!+
SUBROUTINE Cbody(i,x,r,dr)
! ---------------------------------------------------------------------------
! PURPOSE - dummy subroutine for centerbody
  INTEGER,PARAMETER:: SP=KIND(1.0), DP=KIND(1.0D0)   ! Numerical Recipes
  INTEGER,INTENT(IN):: i
  REAL(DP),INTENT(IN):: x
  REAL(DP),INTENT(OUT):: r,dr
!
!----------------------------------------------------------------------------
  IF (i == 0 .OR. x==0.0) THEN 
    r=0.0
    dr=0.0
  ELSE
    r=0.0
    dr=0.0
  END IF
  RETURN
END Subroutine  Cbody    ! -----------------------------------------------------


!+
SUBROUTINE Abody(i,x,r,dr)
! ------------------------------------------------------------------------------
! PURPOSE - dummy subroutine for annulus
  INTEGER,PARAMETER:: SP=KIND(1.0), DP=KIND(1.0D0)   ! Numerical Recipes
  INTEGER,INTENT(IN):: i
  REAL(DP),INTENT(IN):: x
  REAL(DP),INTENT(OUT):: r,dr
!
!----------------------------------------------------------------------------
  IF (i == 0 .OR. x == 0.0) THEN
    r=0.0
    dr=0.0
  ELSE
    r=0.0
    dr=0.0
  END IF
  RETURN
END Subroutine Abody   ! -------------------------------------------------------

END Module InletProcedures   ! =================================================





!+
PROGRAM Inlet
! ------------------------------------------------------------------------------

USE Blank
USE InletProcedures

  IMPLICIT NONE

!!!  EXTERNAL abody,cbody

  INTEGER:: idim
  COMMON/DIM/idim
  REAL(DP):: spacc
  COMMON/SPACC/spacc
!!!  INCLUDE 'blank.cmn'

  REAL(DP):: a,b
  REAL(DP):: dai
  REAL(DP):: dr
  REAL(DP):: dup,sup,wup
  INTEGER:: errCode
  CHARACTER(LEN=80):: fileName

  INTEGER:: iann
  INTEGER:: ip
  INTEGER:: jm
  INTEGER:: km
!  INTEGER:: L   ! see if we can avoid this
  INTEGER:: loopVar   ! used for "tame" loop variable
!  INTEGER:: m
  INTEGER:: n,maxnp
!!!  INTEGER:: na,nb
  INTEGER:: nodis
  REAL(DP):: rb
  REAL(DP),DIMENSION(6):: teg
  REAL(DP):: xb


!----------------------------------------------------------------------
100 FORMAT(7I10)
101 FORMAT(7F10.6)

  DO
    WRITE(*,*) "Enter the name of the input file: "
    READ(*,'(A)') fileName
    IF (LEN_TRIM(fileName) == 0) STOP
    OPEN(UNIT=5, FILE=fileName, IOSTAT=errCode, &
      STATUS='OLD', ACTION='READ', POSITION='REWIND')
    IF (errCode == 0) EXIT
    OPEN(UNIT=5, FILE=Trim(fileName)//".dat", IOSTAT=errCode, &
      STATUS='OLD', ACTION='READ', POSITION='REWIND')
    IF (errCode == 0) EXIT
    WRITE(*,*) "Unable to open this file. Try again."
  END DO
  INQUIRE(UNIT=5, NAME=fileName)
  WRITE(*,*) "Reading from "//Trim(fileName)

  OPEN(UNIT=6, FILE='inlet.out', IOSTAT=errCode, &
    STATUS='REPLACE', ACTION='WRITE', POSITION='REWIND')
  IF (errCode /= 0) THEN
    WRITE(*,*) "Unable to open output file"
    STOP
  END IF

  OPEN(UNIT=DBG, FILE='inlet.dbg', IOSTAT=errCode, &
    STATUS='REPLACE', ACTION='WRITE', POSITION='REWIND')
  IF (errCode /= 0) THEN
    WRITE(*,*) "Unable to open debugging file"
    STOP
  END IF

  OPEN(UNIT=FIG, FILE='inlet.fig', IOSTAT=errCode, &
    STATUS='REPLACE', ACTION='WRITE', POSITION='REWIND')
  IF (errCode /= 0) THEN
    WRITE(*,*) "Unable to open plotting file"
    STOP
  END IF


!!!  CALL Splot(1,a,b)


1 READ(5,'(A)',IOSTAT=errCode) generalTitle     ! many branches to this line
  IF (errCode < 0) STOP "End of File in Input File"
  IF (generalTitle(1:4) == "DONE") STOP "Done"
  last=0

  READ(5,101) teg
  n=teg(1)
  nob=teg(2)
  noa=teg(3)
  maxnp=teg(4)
  nodis=teg(5)
  idim=teg(6)
  IF (idim <= 0) idim=3

  READ(5,101) emin,gamma,sing,theta,xt
  theta=theta*(PI/180)
  IF (maxnp <= 0) maxnp=50
  READ(5,101) test,crmax,coalt,space,spacc

  IF (nob <= 0) THEN
    CALL Cbody(1, xt, r(1,1,1), dr)
  ELSE
    READ(5,101)(ctab(1,loopVar),loopVar=1,nob)
    READ(5,101)(ctab(2,loopVar),loopVar=1,nob)
!    DO loopVar=1,NOB
!      CALL SPLOT(3,CTAB(1,loopVar),CTAB(2,loopVar))
!    END DO
    WRITE(FIG,*) "DATA ", nob
    WRITE(FIG,'(2F15.5)') (ctab(1,loopVar),ctab(2,loopVar),loopVar=1,nob)
!    CALL SPLOT(4,A,B)
!!!    NB=NOB-1
    READ(5,101)(CTAB(3,loopVar),loopVar=1,nob-1)
    XT=CTAB(1,NOB)                          ! last point
  END IF

  IF (noa <= 0) THEN
    CALL ABODY(1,ATAB(1,1),ATAB(2,1),DR)
  ELSE
    READ(5,101)(ATAB(1,loopVar),loopVar=1,NOA)
    READ(5,101)(ATAB(2,loopVar),loopVar=1,NOA)
!    DO loopVar=1,NOA
!      CALL SPLOT(3,ATAB(1,loopVar),ATAB(2,loopVar))
!    END DO
!    CALL SPLOT(4,A,B)
    WRITE(FIG,*) "DATA ", noa
    WRITE(FIG,'(2F15.5)') (atab(1,loopVar),atab(2,loopVar),loopVar=1,noa)

!    NA=NOA-1
    READ (5,101)(ATAB(3,loopVar),loopVar=1,noa-1)
  END IF

  IREG=1
  IRAY=1
  IFAM=1
  i=1
  j=1
  CALL PUNT(7)
  P4=(1.0+0.5*(GAMMA-1.0)*EMIN **2)**(GAMMA/(GAMMA-1.0))  ! ptinf/pinf

  WIN=EMIN**2/(1.0+0.5*(GAMMA-1.0)*EMIN**2)
  WIN=SQRT(WIN)

  IF (n <= 0) THEN
    IANN=1
    CALL CONIC()                      ! use Conic to get a start
    IF (LAST <= 0) GO TO 24
    IF (LAST > 0) GO TO 1              ! aborts this case. Data left unread
  END IF

  IANN=1

  DO K=1,N
    READ (5,101) X(i,J,K),R(i,J,K),DEL(I,J,K),W(I,J,K),S(i,j,k)
    DEL(I,J,K)=0.01745329*DEL(I,J,K)
    CALL PUNT(1)
  END DO

  IF (LAST > 0) GO TO 1

  SCB=S(I,J,1)
  XIN=X(1,1,1)
  ITYPE=1
  write(DBG,*) "ITYPE set to 1 in main program"
  IN=N
  NOP(I,J)=IN


  K=N
  write(DBG,*) "k set to n in main program. Now=", k
  GO TO 24
43 J=J
  K=K
  GO TO (57,58,57,58),j
57 IN=IN+1
58 WUP=W(I,J,K)
   DUP=DEL(I,J,K)
   SUP=S(I,J,K)
   XB=X(I,J,K)
   RB=R(I,J,K)
  IF (I <= 1) GO TO 40
!!!IF (I-1) 40,40,41
   I=1
   write(DBG,*) "I reset to 1"
   IP=2

  DO loopVar=1,9
    ICON(IP,loopVar)=IRR(loopVar)
  END DO
  write(DBG,*) "irr stashed in col ", IP, " of ICON"

  IFAM=1
  IF (nob > 0) GO TO 52
!!  IF (NB) 51,51,52
51 CALL CBODY( 2,XB,RB,DR)
  DAI=ATAN(DR)
  GO TO 42

52 DO loopVar=2,NOB
     IF (XB > CTAB(1,loopVar)) CYCLE
     DAI=0.01745329*CTAB(3,loopVar-1)  ! find first ctab(1,:) > xb
     GO TO 42
   END DO   
   GO TO 1   ! if you never jump to 42, it's all over

40 I=2
   write(DBG,*) "I set to 2 in main program"
   IP=1

  DO loopVar=1,9
    ICON(IP,loopVar)=IRR(loopVar)
  END DO
  write(DBG,*) "irr saved in column ", IP, " of ICON"

  IFAM=2
  IF (noa == 0) THEN
    CALL Abody(2,xb,rb,dr)
    DAI=ATAN(DR)
    GO TO 42
  END IF

48 DO loopVar=2,NOA
     IF (XB >= ATAB(1,loopVar)) CYCLE
     DAI=0.01745329*ATAB(3,loopVar-1)  ! find first atab(1,:) > xb
     GO TO 42
   END DO
   GO TO 1    ! if you never jump to 42 it's all over


42 IREG=IREG+1       ! we have found start of new region at (xb,rb)
  ITYPE=1
  write(DBG,*) "ITYPE reset to 1 in main program"
  J=1
  write(DBG,*) "J set to 1 in main program"
  IRAY=1
  write(DBG,*) "IRAY set to 1 in main program"
  IN=2
  write(DBG,*) "In main program, calling Acray", dai,wup,sup,dup,xb,rb
  CALL ACRAY(DAI,WUP,SUP,DUP,XB,RB)                      ! only call to Acray


24 IRAY=IRAY+1     ! lots of jumps to this line
   write(DBG,*) "IRAY incremented in main program. Now it is ", iray
   IF (last > 0) GO TO 1
   IF (in <=1 ) GO TO 1
  J=J+1
  write(DBG,*) "J incremented in main program. Now, J=",j
  JP=JP+1
  K=1
  write(DBG,*) "k set to 1 in main program"
  kp=0
  GO TO (1,4,5,6,7),J
4 jp=1
6 kp=kp+1
  GO TO 8
7 j=1
  write(DBG,*) "J reset to 1 in main program"
5 GO TO (9,10),ifam
  9 CALL Body(cbody,ctab(:,:),nob)
    GO TO 14
10  CALL Body(abody,atab(:,:),noa)
14  IF (x(i,j,k) > xt) GO TO 1

17  kp=kp+1
    k=k+1
    write(DBG,*) "k incremented in main program. Now=", k
    IF (last > 0) GO TO 1
 8 IF (k > in-1) GO TO 19
   CALL Flow()
   IF (ifam > 0) GO TO 17

33 jm=jp
   km=kp+1
34 x(i,j,k)=x(i,jm,km)
   r(i,j,k)=r(i,jm,km)
   w(i,j,k)=w(i,jm,km)
   s(i,j,k)=s(i,jm,km)
   u(i,j,k)=u(i,jm,km)
   del(i,j,k)=del(i,jm,km)
   km=km+1
   k=k+1
   write(DBG,*) "k incremented after 34 in main program. Now=", k
   IF (km <= nop(i,jp)) GO TO 34

   GO TO (35,37,35,37),J
37 nop(i,j)=in-1
   GO TO 38
35 in=in-1
   nop(i,j)=in

38 ifam=-ifam
   kp=km-2
   k=k-1
   write(DBG,*) "k decremented in main program. Now=", k
   GO TO 60

19 nop(i,j)=in-1
   GO TO (20,32,20,32),j
32 IF (itype /= 1) GO TO 24
29 nop(i,j)=in
   in=in+1
   IF (in > 50) THEN
     CALL ErrorMessage(1) ! THE NUMBER OF POINTS IN A RAY EXCEEDS 50.
     GO TO 1
   ELSE
     GO TO 31
   END IF

20 IF (itype-2) 21,22,23
21 nop(i,j)=in
31 CALL Shock(dup)
   IF (last > 0) GO TO 1
   IF (itype /= 1) GO TO 43    ! big jump back to 43

44 IF (x(i,j,k) >= xt) GO TO 25

60 GO TO (61,24),iann        ! big jump back to 24

61 IF (x(i,j,k) < atab(1,1).AND. r(i,j,k) < atab(2,1)) GO TO 80
62 CALL Flint()
   IF (last > 0) GO TO 1
   IF (itype == 1) GO TO 80

   iann=2
   GO TO 43
25 ITYPE=2
   write(DBG,*) "ITYPE set to 2 in main program"
   GO TO 24
22 IN=IN-1
   GO TO 24
23 NOP(I,J)=IN
   GO TO (26,27),IFAM
26 CALL Body(ABODY, atab(:,:), NOA)
   GO TO 28
27 CALL BODY(CBODY, ctab(:,:), NOB)
28 IF (X(I,J,K)-XT) 24,1,1    ! big jump back to 24

80 J=j
   GO TO (82,24,82,24),J
82 IF (IN-MAXNP) 24,83,81
!!!ERROR CODE-1.  THE NUMBER OF POINTS IN i
!!!     NUMBER OF POINTS ALLOWED IN A RAY (INPL
81 CALL ErrorMessage(1)
   GO TO 1
83 K=1
   write(DBG,*) "k set to 1 in main program (83)"
   IF (NODIS <= 0) THEN
     CALL ErrorMessage(1)
     GO TO 1
   END IF
   KP=2+NODIS
   IF (MOD(IN,NODIS+1) .NE. 1) GO TO 89
   WRITE(DBG,*) "In main, moving arrays by NODIS=", nodis
   DO 84 K=2,50                 ! k is global
     X(i,J,K)=X(I,J,KP)
     R(i,J,K)=R(i,J,KP)
     DEL(I,J,K)=DEL(i,J,KP)
     W(i,J,K)=W(I,J,KP)
     S(i,J,K)=S(I,J,KP)
     U(i,J,K)=U(I,J,KP)
     NOP(I,J)=K
     KP=KP+NODIS+1
     IF (KP > MAXNP) GO TO 89
84 END DO

89 SPACE=2.0**NODIS*SPACE
   IN=NOP(I,J)
   GO TO 24

END Program Inlet

