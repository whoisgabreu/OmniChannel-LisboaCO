// Troca de tela
function mostrarTela(idTela) {
  document.querySelectorAll(".tela").forEach(tela => {
    tela.style.display = "none"
  });
  document.getElementById(idTela).style.display = "block";
}


let cardsFiltrados = []; // ← Global
let todosCards = [];  // Para armazenar todos os cards


async function carregarCards() {
  const response = await fetch('/get_cards');
  todosCards = await response.json();
  cardsFiltrados = todosCards;
  renderizarCards(todosCards);
  await prepararFiltros(); // <- aqui você popula os dropdowns
}

function renderizarCards(cards) {
  const container = document.getElementById("cards-frame");
  container.innerHTML = ""; // limpa antes de renderizar de novo

  document.getElementById("contador-resultados").textContent = `Total de cards: ${cards.length}`;

  cards.forEach(card => {
    const cardElement = document.createElement("div");
    cardElement.className = "card";

    cardElement.innerHTML = `

      <div class="card-content" role="button" onclick="mostrarDetalhesDoCard(${card.id})">
        <div class="card-info">
        
          <p><b>CNPJ:</b> ${card["Cliente - CNPJ"]}</p>
          <p><b>Cliente:</b> ${card["title"]}</p>
          <p><b>Contrato</b>: ${card["Contrato - Modelo de Pagamento"]}</p>
          <p><b>Squad</b>: ${card["Squad Atribuída"]}</p>
          <p><b>Fase Atual</b>: ${card["fase"]}</p>

        </div>
      </div>
            `;
    
    container.appendChild(cardElement);
  });
}

function clicarNoCard(id) {
  // alert(`Você clicou no card de ID ${id}`);
  const card = todosCards.find(c => c.id == id)
  if (card) {
    console.log("Card localizado:", card)
    window.open(`https://app.pipefy.com/open-cards/${id}`)
  } else {
    console.warn("Card não encontrado com ID:", id)
  }
}


function mostrarDetalhesDoCard(id) {
  const card = todosCards.find(c => c.id == id);
  const detalhes = document.getElementById("details-frame");

  if (!card) return;

  detalhes.innerHTML = `<h2>${card.title}</h2>`;

  for (let chave in card) {
    if (chave === "title" || chave === "id") continue;
    let valor = card[chave];
    let valorFormatado = "";
    // Tenta converter para array JSON, se possível
    try {
      const parsed = JSON.parse(valor);
      if (Array.isArray(parsed)) {
        valorFormatado = `<ul>` + parsed.map(item => `<li>${item}</li>`).join("") + `</ul>`;
      } else {
        valorFormatado = parsed;
      }
    } catch (_) {
      // Se for link
      if (typeof valor === "string" && valor.startsWith("http")) {
        valorFormatado = `<a href="${valor}" target="_blank">${valor}</a>`;
      } else {
        valorFormatado = valor || "-";
      }
    }

    detalhes.innerHTML += `
      <div class="campo">
        <h3>${chave}</h3>
        <div>${valorFormatado}</div>
      </div>
    `;
  }

  detalhes.innerHTML += `
    <button onclick="window.open('https://app.pipefy.com/open-cards/${card.id}', '_blank')">Abrir no Pipefy</button>
  `;
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
  const squads = await carregarLista(todosCards, "Squad Atribuída");
  const unidades = await carregarLista(todosCards, "Unidade Atribuída");
  const pagamentos = await carregarLista(todosCards, "Contrato - Modelo de Pagamento");
  const fases = await carregarLista(todosCards, "fase");

  await renderizarLista(squads, "filtroSquad");
  await renderizarLista(unidades, "filtroUnidade");
  await renderizarLista(pagamentos, "filtroPagamento");
  await renderizarLista(fases, "filtroFase");
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

document.getElementById("searchInput").addEventListener("input", aplicarFiltro);
document.getElementById("filtroSquad").addEventListener("change", aplicarFiltro);
document.getElementById("filtroUnidade").addEventListener("change", aplicarFiltro);
document.getElementById("filtroPagamento").addEventListener("change", aplicarFiltro);
document.getElementById("filtroFase").addEventListener("change", aplicarFiltro);

function aplicarFiltro() {
  const termo = document.getElementById("searchInput").value.toLowerCase();
  const filtroSquad = document.getElementById("filtroSquad").value.toLowerCase();
  const filtroUnidade = document.getElementById("filtroUnidade").value.toLowerCase();
  const filtroPagamento = document.getElementById("filtroPagamento").value.toLowerCase()
  const filtroFase = document.getElementById("filtroFase").value.toLowerCase()

  const filtrados = todosCards.filter(card => {
    const matchesTexto =
      (card["title"] && card["title"].toLowerCase().includes(termo)) ||
      (card["id"] && card["id"].toString().includes(termo)) ||
      (card["Cliente - CNPJ"] && card["Cliente - CNPJ"].toLowerCase().includes(termo)) ||
      (card["Squad Atribuída"] && card["Squad Atribuída"].toLowerCase().includes(termo)) ||
      (card["Unidade Atribuída"] && card["Unidade Atribuída"].toLowerCase().includes(termo));


    const matchesSquad = !filtroSquad || (card["Squad Atribuída"] && card["Squad Atribuída"].toLowerCase().includes(filtroSquad));
    const matchesUnidade = !filtroUnidade || (card["Unidade Atribuída"] && card["Unidade Atribuída"].toLowerCase().includes(filtroUnidade));
    const matchesPagamento = !filtroPagamento || (card["Contrato - Modelo de Pagamento"] && card["Contrato - Modelo de Pagamento"].toLowerCase().includes(filtroPagamento));
    const matchesFase = !filtroFase || (card["fase"] && card["fase"].toLowerCase().includes(filtroFase));

    return matchesTexto && matchesSquad && matchesUnidade && matchesPagamento && matchesFase;
  });
  cardsFiltrados = filtrados;
  console.log(cardsFiltrados.length)
  renderizarCards(filtrados);
}


function exportarParaExcel(dados, nomeArquivo = "cards_filtrados.xlsx") {
  if (!dados.length) return alert("Nenhum dado para exportar!");

  const ws = XLSX.utils.json_to_sheet(dados);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, "Cards");

  XLSX.writeFile(wb, nomeArquivo);
}


carregarCards();
