flowchart TB
    Start([Inicio Sesión]) --> Greeting
    
    subgraph Phases [Fases de Servicio]
        Greeting[GREETING] --> |Cliente se sienta| Drinks
        Drinks[DRINKS] --> |Pide bebida| Tapas
        Tapas[TAPAS] --> |Pide picoteo| Mains
        Mains[MAINS] --> |Pide plato fuerte| Check
        Check[CHECK] --> |Espera / Come| Dessert
        Dessert[DESSERT] --> |Pide/Rechaza postre| Coffee
        Coffee[COFFEE] --> |Pide/Rechaza café| Bill
        Bill[BILL] --> |Pide cuenta| Farewell
    end
    
    subgraph Signals [Señales NLP]
        Hurry[Prisa] --> |Acelera| Bill
        Celeb[Celebración] --> |Añade| Dessert
        BillReq[Pide Cuenta] --> |Salta a| Bill
    end
    
    subgraph Logic [Cerebro de Sugerencias]
        T1{Tiempo > 5min?}
        T2{Tiempo > 15min?}
        W{Clima?}
        P{Preferencia?}
        
        Drinks --> T1
        T1 --> |Si| SuggestTapas[Sugerir Tapas]
        Tapas --> T2
        T2 --> |Si| SuggestMains[Sugerir Principales]
        Check --> SuggestDessert[Sugerir Postre]
    end
    
    SuggestTapas -.-> Tapas
    SuggestMains -.-> Mains
    SuggestDessert -.-> Dessert
    Farewell --> End([Fin Sesión])
