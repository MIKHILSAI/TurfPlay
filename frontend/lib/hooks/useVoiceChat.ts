"use client"

import { useCallback, useRef, useState } from "react"

export function useVoiceChat(apiBase: string) {
  const [recording, setRecording] = useState(false)
  const [transcribing, setTranscribing] = useState(false)
  const [speaking, setSpeaking] = useState(false)
  const recorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const currentAudioRef = useRef<HTMLAudioElement | null>(null)

  const startRecording = useCallback(
    async (onTranscribed: (text: string) => void) => {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mimeType = MediaRecorder.isTypeSupported("audio/webm")
        ? "audio/webm"
        : "audio/mp4"

      const recorder = new MediaRecorder(stream, { mimeType })
      chunksRef.current = []

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }

      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop())
        const blob = new Blob(chunksRef.current, { type: mimeType })

        setTranscribing(true)
        try {
          const form = new FormData()
          form.append("file", blob, "audio.webm")

          const res = await fetch(`${apiBase}/speech/transcribe`, {
            method: "POST",
            body: form,
          })

          if (res.ok) {
            const data = await res.json()
            if (data.text?.trim()) onTranscribed(data.text.trim())
          }
        } catch (err) {
          console.error("STT failed:", err)
        } finally {
          setTranscribing(false)
        }
      }

      recorderRef.current = recorder
      recorder.start()
      setRecording(true)
    },
    [apiBase]
  )

  const stopRecording = useCallback(() => {
    recorderRef.current?.stop()
    setRecording(false)
  }, [])

  const speak = useCallback(
    async (text: string) => {
      if (!text?.trim()) return
      setSpeaking(true)
      try {
        // Stop any previous playback
        if (currentAudioRef.current) {
          currentAudioRef.current.pause()
          currentAudioRef.current = null
        }

        const res = await fetch(`${apiBase}/speech/synthesize`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text }),
        })
        if (!res.ok) throw new Error("TTS failed")

        const blob = await res.blob()
        const url = URL.createObjectURL(blob)
        const audio = new Audio(url)
        currentAudioRef.current = audio

        audio.onended = () => {
          URL.revokeObjectURL(url)
          currentAudioRef.current = null
        }

        await audio.play()
      } catch (err) {
        console.error("TTS failed:", err)
      } finally {
        setSpeaking(false)
      }
    },
    [apiBase]
  )

  return {
    recording,
    transcribing,
    speaking,
    startRecording,
    stopRecording,
    speak,
  }
}