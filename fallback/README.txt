Place your fallback audio file here as "fallback.mp3".

This file is played when the main pipeline fails (no internet, OpenAI down, etc.).

Suggested content for the fallback audio:
  "Bom dia. O briefing automático não está disponível hoje. Verifique sua conexão
   com a internet ou o status dos serviços. Tenha um bom dia."

You can generate this file once with:
  python -c "
  from openai import OpenAI
  client = OpenAI()
  with client.audio.speech.with_streaming_response.create(
      model='tts-1',
      voice='nova',
      input='Bom dia. O briefing automático não está disponível hoje. Verifique sua conexão com a internet ou o status dos serviços. Tenha um bom dia.',
  ) as r:
      r.stream_to_file('fallback/fallback.mp3')
  "
