
export async function copyToClipboard(text: string): Promise<boolean> {
  if (navigator.clipboard && window.isSecureContext) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (err) {
      console.error("Erro ao copiar via navigator.clipboard:", err);
    }
  }

  // Fallback: execCommand('copy') - funciona em HTTP
  try {
    const textArea = document.createElement("textarea");
    textArea.value = text;

    // Garante que o elemento não seja visível mas esteja no DOM
    textArea.style.position = "fixed";
    textArea.style.left = "-999999px";
    textArea.style.top = "-999999px";
    document.body.appendChild(textArea);

    textArea.focus();
    textArea.select();

    const successful = document.execCommand("copy");
    document.body.removeChild(textArea);
    return successful;
  } catch (err) {
    console.error("Erro ao copiar via fallback:", err);
    return false;
  }
}
