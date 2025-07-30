function mostrarDetalhesDoCard(id) {
  const card = todosCards.find(c => c.id == id);
  const detalhes = document.getElementById("details-frame");

  if (!card) return;

  detalhes.innerHTML = `

    <form method="POST" action="/atualizar_usuario/${card.id}">
        <div class="register-field">

            <label for="Nome">Nome: </label>
            <input class="text-input" type="text" name="nome" required value="${card.nome}">

            <label for="E-mail">E-mail: </label>
            <input class="text-input" type="email" name="email" required value="${card.email}">

            <label for="Cargo">Cargo: </label>
            <input class="text-input" type="text" name="cargo" required value="${card.cargo}">
            
            <div>
              <label for="admin">Admin? </label>
              <input class="checkbox-input" type="checkbox" name="admin" ${card.admin ? "checked" : ""}>
            </div>

            <div>
              <label for="ativo">Ativo? </label>
              <input class="checkbox-input" type="checkbox" name="ativo" ${card.ativo ? "checked" : ""}>
            </div>

            <div class="select-container">
                <label for="Squad">Squad:</label><br>
                <select id="squad" name="squad">
                    <option value="${card.squad}">${card.squad}</option>
                    <option value="Tecnologia">Tecnologia</option>
                    <option value="Shark">Shark</option>
                    <option value="Internacional">Internacional</option>
                    <option value="Capivaras">Capivaras</option>
                    <option value="Xeque Mate">Xeque Mate</option>
                    <option value="Midas">Midas</option>
                    <option value="São Bento">São Bento</option>
                    <option value="Carcará">Carcará</option>
                    <option value="Comercial">Comercial</option>
                    <option value="Balneário">Balneário</option>
                    <option value="X Lite">X Lite</option>
                    <option value="Águia">Águia</option>
                </select>
            </div>

            <div class="select-container">
                <label for="Unidade">Unidade:</label><br>
                <select id="unidade" name="unidade">
                    <option value="${card.unidade}">${card.unidade}</option>
                    <option value="Pampulha">Pampulha</option>
                    <option value="Balneário">Balneário</option>
                    <option value="São Bento">São Bento</option>
                    <option value="Goiânia">Goiânia</option>
                </select>
            </div>

            
            <button type="submit">Atualizar</button>
            
            </div>

    </form>
    <form method="POST" action="/resetar-senha/${card.id}">
        <button type="submit">Resetar senha</button>
    </form>

  `;
}



let todosCards = [];  // Para armazenar todos os cards


async function carregarCards() {
  const response = await fetch('/usuarios');
  todosCards = await response.json();
  renderizarCards(todosCards);
  await prepararFiltros(); // <- aqui você popula os dropdowns
}

function renderizarCards(cards) {
  const container = document.getElementById("cards-frame");
  container.innerHTML = ""; // limpa antes de renderizar de novo

  cards.forEach(card => {
    const cardElement = document.createElement("div");
    cardElement.className = "card";

    cardElement.innerHTML = `

      <div class="card-content" role="button" onclick="mostrarDetalhesDoCard(${card.id})">
        <div class="card-info">
        
            <p><b>Nome:</b> ${card["nome"]}</p>
            <p><b>E-mail:</b> ${card["email"]}</p>
            <p><b>Unidade</b>: ${card["unidade"]}</p>
            <p><b>Squad</b>: ${card["squad"]}</p>
            </div>
            </div>
            `;
            
    container.appendChild(cardElement);
  });
}

// Alterar Classe de elemento

function toggleClasse() {
  const menu = document.querySelector('.menu');
  const sidebar = document.querySelector('.sidebar');
  const mainContent = document.querySelector('.main-content');

  menu.classList.toggle("change");
  sidebar.classList.toggle('change');
  mainContent.classList.toggle('change');
}

// -------------

// Esconder div de nova senha

function esconderDiv() {
  document.getElementById("box-reset").style.display = "none";
}



// Cria lista com os dados da chave desejada do dicionário
async function carregarLista(cards, chaveDict) {
  const squadsSet = new Set();
  cards.forEach(card => {
    const squad = card[chaveDict];
    if (squad) {
      squadsSet.add(squad);
    }
  });
  return Array.from(squadsSet); // converte o Set de volta para array
}

async function renderizarLista(lista, selectId) {
  const select = document.getElementById(selectId);

  lista.forEach(item => {
    const selectOpt = document.createElement("option");
    selectOpt.value = item;
    selectOpt.innerText = item;
    select.appendChild(selectOpt);
  });
}

async function prepararFiltros() {
  const squads = await carregarLista(todosCards, "squad");
  const unidades = await carregarLista(todosCards, "unidade");
  const pagamentos = await carregarLista(todosCards, "cargo");

  await renderizarLista(squads, "filtroSquad");
  await renderizarLista(unidades, "filtroUnidade");
  await renderizarLista(pagamentos, "filtroCargo");
}



document.getElementById("searchInput").addEventListener("input", aplicarFiltro);
document.getElementById("filtroSquad").addEventListener("change", aplicarFiltro);
document.getElementById("filtroUnidade").addEventListener("change", aplicarFiltro);
document.getElementById("filtroCargo").addEventListener("change", aplicarFiltro);

function aplicarFiltro() {
  const termo = document.getElementById("searchInput").value.toLowerCase();
  const filtroSquad = document.getElementById("filtroSquad").value.toLowerCase();
  const filtroUnidade = document.getElementById("filtroUnidade").value.toLowerCase();
  const filtroCargo = document.getElementById("filtroCargo").value.toLowerCase()

  const filtrados = todosCards.filter(card => {
    const matchesTexto =
      (card["nome"] && card["nome"].toLowerCase().includes(termo)) ||
      (card["email"] && card["email"].toString().includes(termo));


    const matchesSquad = !filtroSquad || (card["squad"] && card["squad"].toLowerCase().includes(filtroSquad));
    const matchesUnidade = !filtroUnidade || (card["unidade"] && card["unidade"].toLowerCase().includes(filtroUnidade));
    const matchesCargo = !filtroCargo || (card["cargo"] && card["cargo"].toLowerCase().includes(filtroCargo));

    return matchesTexto && matchesSquad && matchesUnidade && matchesCargo;
  });

  renderizarCards(filtrados);
}


carregarCards();