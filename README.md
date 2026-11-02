# Tapa Solver Determinístico

Motor tradicional de Tapa, separado do TapaEvolve. Aplica as regras até não
haver mais deduções; quando necessário, tenta a primeira casa desconhecida na
ordem linha a linha, primeiro preta e depois branca, com backtracking.
Não contém LLM, expressão de pontuação ou seleção aprendida de células.

## Onde estão as funções

- `src/tapa_solver_deterministico/propagation.py`: `propagate(board)` aplica
  as regras a um tabuleiro, preenchendo somente casas dedutíveis.
- `src/tapa_solver_deterministico/solver.py`: `solve(puzzle)` coordena a
  propagação e a busca em ordem fixa até obter um tabuleiro completo.
- `src/tapa_solver_deterministico/verifier.py`:
  `DeterministicRulesEngine.validate(board)` confere uma solução pronta.
- `src/tapa_solver_deterministico/api.py`: `POST /api/solve` expõe o motor ao
  frontend, com o mesmo formato de entrada e saída do TapaEvolve para
  resolução individual.

O motor inclui ainda `model.py` e `patterns.py`, necessários para representar
o tabuleiro e interpretar as pistas. As regras e estruturas vieram do projeto
TapaEvolve; o resolvedor e a API foram reduzidos à estratégia tradicional.

## Executar no Windows

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
tapa-solver-api
```

A documentação da API fica em <http://127.0.0.1:8002/docs>. O serviço usa a
porta 8002 para poder rodar ao lado do TapaEvolve na porta 8001.

## Conectar ao frontend integrado

No arquivo `assets/config.js` do frontend local, altere `apiBaseUrl` para
`http://127.0.0.1:8002`. Recarregue a página e deixe o toggle **Heurística de
escolha** desligado (**Escolha simples**). A tela de resolução enviará
`heuristic: "first"` e exibirá solução, nós, backtracks e tempo.

Para voltar ao TapaEvolve, restaure a URL `http://127.0.0.1:8001`. A tela
**Avaliação de Heurísticas** pertence ao TapaEvolve e não é oferecida por este
serviço.

## Chamada de exemplo

```python
from tapa_solver_deterministico import Puzzle, solve

puzzle = Puzzle(rows=2, cols=2, clues={(0, 0): (1,)})
result = solve(puzzle)
print(result.solved, result.board.render() if result.board else result.message)
```

Os limites padrão são 120 segundos e 1 milhão de nós por tabuleiro. Um
`timeout` significa que não se encontrou uma solução dentro desse orçamento,
não que o tabuleiro não tenha solução.

