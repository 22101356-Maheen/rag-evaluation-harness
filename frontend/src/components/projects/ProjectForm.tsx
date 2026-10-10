import { useState } from 'react'
import type { FormEvent } from 'react'

export type ProjectDraft = { name: string; description: string }
type ProjectFormProps = { onCancel: () => void; onSubmit?: (draft: ProjectDraft) => void }

export default function ProjectForm({ onCancel, onSubmit }: ProjectFormProps) {
  const [message, setMessage] = useState('')

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = event.currentTarget
    const nameInput = form.elements.namedItem('projectName') as HTMLInputElement
    nameInput.setCustomValidity(nameInput.value.trim() ? '' : 'Enter a project name.')
    if (!form.reportValidity()) return
    const descriptionInput = form.elements.namedItem('description') as HTMLTextAreaElement
    if (onSubmit) onSubmit({ name: nameInput.value.trim(), description: descriptionInput.value.trim() })
    else setMessage('Project creation is not connected. This draft has not been saved.')
  }

  return (
    <form className="form-stack" onSubmit={submit}>
      <div className="field"><label htmlFor="project-name">Project name</label><input id="project-name" name="projectName" required maxLength={200} placeholder="Give your project a name" onInput={event => event.currentTarget.setCustomValidity('')} /></div>
      <div className="field"><label htmlFor="project-description">Description <span className="optional-label">(optional draft note)</span></label><textarea id="project-description" name="description" rows={3} maxLength={1000} placeholder="What will you evaluate?" /><p>Kept in this form only. Nothing is saved yet.</p></div>
      <p className="form-status" role="status">{message}</p>
      <div className="form-actions"><button className="button button-secondary" type="button" onClick={onCancel}>Cancel</button><button className="button button-primary" type="submit">Create Project</button></div>
    </form>
  )
}
