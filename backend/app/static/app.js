const form = document.getElementById("register-form");
const submit = document.getElementById("submit");
const formMessage = document.getElementById("form-message");
const apiStatus = document.getElementById("api-status");

const fields = {
  username: document.getElementById("username"),
  password: document.getElementById("password"),
  confirmation: document.getElementById("confirmation"),
};

function setApiStatus(state, text) {
  apiStatus.dataset.state = state;
  apiStatus.textContent = text;
}

async function refreshApiStatus() {
  try {
    const response = await fetch("/health");
    if (!response.ok) {
      throw new Error(`status ${response.status}`);
    }
    const { version } = await response.json();
    setApiStatus("online", `API no ar · versão ${version}`);
  } catch {
    setApiStatus("offline", "API indisponível");
  }
}

function setFieldError(name, text) {
  const input = fields[name];
  const error = document.getElementById(`${name}-error`);
  error.textContent = text;
  error.hidden = !text;
  if (text) {
    input.setAttribute("aria-invalid", "true");
  } else {
    input.removeAttribute("aria-invalid");
  }
}

function showFormMessage(kind, text) {
  formMessage.dataset.kind = kind;
  formMessage.textContent = text;
  formMessage.hidden = false;
  formMessage.focus();
}

function clearMessages() {
  formMessage.hidden = true;
  Object.keys(fields).forEach((name) => setFieldError(name, ""));
}

function validate(username, password, confirmation) {
  const errors = {};
  if (username.length < 3 || username.length > 50) {
    errors.username = "Use um nome de usuário de 3 a 50 caracteres.";
  }
  if (password.length < 8) {
    errors.password = "Use uma senha com pelo menos 8 caracteres.";
  }
  if (password !== confirmation) {
    errors.confirmation = "As senhas não são iguais. Digite a mesma senha nos dois campos.";
  }
  return errors;
}

async function register(username, password) {
  const response = await fetch("/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });

  if (response.status === 201) {
    form.reset();
    showFormMessage("success", `Conta criada para ${username}. O login estará disponível em uma versão futura.`);
  } else if (response.status === 409) {
    setFieldError("username", "Esse nome de usuário já está em uso. Escolha outro.");
    fields.username.focus();
  } else if (response.status === 422) {
    showFormMessage("error", "A API recusou os dados informados. Confira os campos e tente de novo.");
  } else {
    showFormMessage("error", "A API não conseguiu criar a conta. Tente de novo em alguns instantes.");
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearMessages();

  const username = fields.username.value.trim();
  const password = fields.password.value;
  const errors = validate(username, password, fields.confirmation.value);
  const invalidFields = Object.keys(errors);

  if (invalidFields.length > 0) {
    invalidFields.forEach((name) => setFieldError(name, errors[name]));
    fields[invalidFields[0]].focus();
    return;
  }

  submit.disabled = true;
  submit.textContent = "Criando conta…";

  try {
    await register(username, password);
  } catch {
    showFormMessage("error", "Não foi possível falar com a API. Verifique se ela está no ar e tente de novo.");
  } finally {
    submit.disabled = false;
    submit.textContent = "Criar conta";
    refreshApiStatus();
  }
});

refreshApiStatus();
