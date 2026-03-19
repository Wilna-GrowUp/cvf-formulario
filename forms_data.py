FORM_TITLE = "Diagnóstico de Cultura Organizacional baseado no CVF"

FORM_DESCRIPTION = (
    "Este formulário tem como objetivo identificar como a cultura organizacional "
    "é percebida atualmente e como ela idealmente deveria ser, com base no modelo CVF."
)

FORM_INSTRUCTIONS = [
    "Leia com atenção as quatro afirmações de cada dimensão.",
    "Distribua 100 pontos entre as quatro afirmações na coluna Cenário Atual, de acordo com a forma como você percebe a organização hoje.",
    "Distribua 100 pontos entre as quatro afirmações na coluna Cenário Ideal, de acordo com a forma como você acredita que a organização deveria ser.",
    "Em cada dimensão, a soma da coluna Atual deve ser exatamente 100.",
    "Em cada dimensão, a soma da coluna Ideal deve ser exatamente 100.",
    "Use apenas números inteiros positivos ou zero.",
]

DIMENSIONS = [
    {
        "id": "caracteristicas_dominantes",
        "title": "Características dominantes",
        "statements": [
            "A empresa é um ambiente bastante pessoal e acolhedor. Funciona como uma grande família, onde as pessoas compartilham experiências e se apoiam mutuamente.",
            "A empresa é dinâmica e empreendedora. Valoriza a inovação e incentiva as pessoas a assumirem riscos e buscarem novas soluções.",
            "A empresa é orientada para resultados. Há forte foco no alcance de metas, e as pessoas tendem a ser competitivas e voltadas ao desempenho.",
            "A empresa é estruturada e controlada. As atividades são orientadas por procedimentos formais e regras bem definidas.",
        ],
    },
    {
        "id": "lideranca",
        "title": "Liderança",
        "statements": [
            "A liderança na empresa é percebida como orientadora e apoiadora, atuando como mentora, facilitadora e promotora do desenvolvimento das pessoas.",
            "A liderança na empresa é percebida como inovadora e empreendedora, incentivando novas ideias, mudanças e a disposição para assumir riscos.",
            "A liderança na empresa é percebida como focada em resultados, com postura exigente, competitiva e orientada ao alcance de metas.",
            "A liderança na empresa é percebida como organizadora e coordenadora, valorizando eficiência, controle e bom funcionamento dos processos.",
        ],
    },
    {
        "id": "gestao_de_pessoas",
        "title": "Estilo de gestão de pessoas",
        "statements": [
            "O estilo de gestão é caracterizado pelo trabalho em equipe, pela participação e pela busca de consenso nas decisões.",
            "O estilo de gestão é caracterizado pela valorização da iniciativa individual, da inovação, da liberdade e da criatividade.",
            "O estilo de gestão é caracterizado por alta exigência de desempenho, competitividade e forte orientação para resultados.",
            "O estilo de gestão é caracterizado pela estabilidade, previsibilidade e conformidade com normas e procedimentos estabelecidos.",
        ],
    },
    {
        "id": "fator_de_coesao",
        "title": "Fator de coesão",
        "statements": [
            "O que mantém a empresa unida é a lealdade e a confiança mútua. O comprometimento das pessoas com a empresa é elevado.",
            "O que mantém a empresa unida é o compromisso com a inovação e o desenvolvimento. Há forte incentivo à busca por novas ideias e à vanguarda.",
            "O que mantém a empresa unida é o foco em resultados e no cumprimento de metas. O alcance de objetivos é o principal fator de integração.",
            "O que mantém a empresa unida são regras, normas e políticas formais. A estabilidade e o bom funcionamento da empresa são valorizados.",
        ],
    },
    {
        "id": "foco_estrategico",
        "title": "Foco estratégico",
        "statements": [
            "A empresa enfatiza o desenvolvimento das pessoas. Há um ambiente de confiança, abertura e participação.",
            "A empresa enfatiza a busca por novas oportunidades, a inovação e a aquisição de novos recursos. Experimentação e novos desafios são valorizados.",
            "A empresa enfatiza a competitividade e o alcance de resultados. A expansão e o desempenho no mercado são prioridades.",
            "A empresa enfatiza a estabilidade, eficiência e controle. A previsibilidade e o bom funcionamento das operações são valorizados.",
        ],
    },
    {
        "id": "definicao_de_sucesso",
        "title": "Definição de sucesso",
        "statements": [
            "A empresa define o sucesso com base no desenvolvimento das pessoas, no trabalho em equipe, no comprometimento dos colaboradores e na valorização das relações humanas.",
            "A empresa define o sucesso com base na inovação e na oferta de produtos ou serviços diferenciados. Ser referência e líder em inovação é considerado fundamental.",
            "A empresa define o sucesso com base no desempenho no mercado, na superação da concorrência e no alcance de resultados superiores.",
            "A empresa define o sucesso com base na eficiência operacional. Entregas confiáveis, processos bem estruturados e redução de custos são essenciais.",
        ],
    },
]