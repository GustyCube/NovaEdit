import * as vscode from "vscode";

export function activate(context: vscode.ExtensionContext) {
  const disposable = vscode.commands.registerCommand("novaedit.fixCode", async () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
      vscode.window.showErrorMessage("NovaEdit: open a file first.");
      return;
    }

    const config = vscode.workspace.getConfiguration("novaedit");
    const endpoint = process.env.NOVAEDIT_URL || config.get<string>("endpoint", "http://localhost:8000/v1/edit");
    const instruction = config.get<string>("instruction", "fix errors only");

    const doc = editor.document;
    const selection = editor.selection;
    const startLine = Math.min(selection.start.line, selection.end.line);
    const endLine = Math.max(selection.start.line, selection.end.line);
    const code = doc.getText(new vscode.Range(startLine, 0, endLine + 1, 0));

    const diagnostics = vscode.languages
      .getDiagnostics(doc.uri)
      .filter((d) => d.range.start.line >= startLine && d.range.end.line <= endLine + 1)
      .map((d) => d.message);

    const payload = {
      language: doc.languageId,
      code,
      file_path: doc.fileName,
      start_line: startLine + 1,
      end_line: endLine + 1,
      diagnostics,
      instruction
    };

    try {
      await vscode.window.withProgress(
        {
          location: vscode.ProgressLocation.Notification,
          title: "NovaEdit: Generating patch...",
          cancellable: false
        },
        async () => {
          const res = await fetch(endpoint, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
          });
          if (!res.ok) {
            const text = await res.text();
            vscode.window.showErrorMessage(`NovaEdit failed: ${res.status} ${text}`);
            return;
          }
          const body = await res.json();
          const workspaceEdit = new vscode.WorkspaceEdit();
          for (const edit of body.edits) {
            const range = new vscode.Range(edit.start_line - 1, 0, edit.end_line, 0);
            workspaceEdit.replace(doc.uri, range, edit.replacement);
          }
          await vscode.workspace.applyEdit(workspaceEdit);
        }
      );
    } catch (err: any) {
      vscode.window.showErrorMessage(`NovaEdit error: ${err?.message ?? err}`);
    }
  });

  context.subscriptions.push(disposable);
}

export function deactivate() {}
