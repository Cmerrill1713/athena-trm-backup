import { getCurrentWindow } from '@electron/remote'
import { CheckIcon, CodeBracketIcon, DocumentDuplicateIcon, EyeIcon, SparklesIcon, SpeakerWaveIcon } from '@heroicons/react/24/outline'
import copy from 'copy-to-clipboard'
import Store from 'electron-store'
import { useState } from 'react'

// import AthenaIcon from './athena.svg'

const store = new Store()

enum Step {
  WELCOME = 0,
  CLI,
  CAPABILITIES,
  FINISH,
}

export default function () {
  const [step, setStep] = useState<Step>(Step.WELCOME)
  const [commandCopied, setCommandCopied] = useState<boolean>(false)
  const [voiceEnabled, setVoiceEnabled] = useState<boolean>(false)
  const [visionEnabled, setVisionEnabled] = useState<boolean>(false)

  const command = 'athena chat qwen2.5:7b "Hello Athena!"'

  return (
    <div className='drag'>
      <div className='mx-auto flex min-h-screen w-full flex-col bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900'>
        {step === Step.WELCOME && (
          <>
            {/* Header with toggles */}
            <div className='flex items-center justify-between p-4 border-b border-blue-800/30'>
              <h1 className='text-xl font-bold text-white'>Athena</h1>
              <div className='flex gap-4'>
                <div className='flex items-center gap-2'>
                  <SpeakerWaveIcon className={`h-5 w-5 ${voiceEnabled ? 'text-green-400' : 'text-gray-400'}`} />
                  <label className='flex items-center gap-2 text-blue-100 text-sm'>
                    <input
                      type='checkbox'
                      checked={voiceEnabled}
                      onChange={(e) => setVoiceEnabled(e.target.checked)}
                      className='w-4 h-4 rounded border-2 border-blue-300 bg-transparent checked:bg-blue-500 checked:border-blue-500 focus:ring-2 focus:ring-blue-300'
                    />
                    Voice
                  </label>
                </div>
                
                <div className='flex items-center gap-2'>
                  <EyeIcon className={`h-5 w-5 ${visionEnabled ? 'text-green-400' : 'text-gray-400'}`} />
                  <label className='flex items-center gap-2 text-blue-100 text-sm'>
                    <input
                      type='checkbox'
                      checked={visionEnabled}
                      onChange={(e) => setVisionEnabled(e.target.checked)}
                      className='w-4 h-4 rounded border-2 border-blue-300 bg-transparent checked:bg-blue-500 checked:border-blue-500 focus:ring-2 focus:ring-blue-300'
                    />
                    Vision
                  </label>
                </div>
              </div>
            </div>

            {/* Chat Interface */}
            <div className='flex-1 flex flex-col'>
              {/* Messages Area */}
              <div className='flex-1 p-6 overflow-y-auto'>
                <div className='space-y-4'>
                  <div className='flex justify-start'>
                    <div className='bg-blue-800/30 rounded-lg p-4 max-w-[80%]'>
                      <p className='text-blue-100'>
                        Welcome to Athena! I'm your AI assistant with advanced capabilities. 
                        How can I help you today?
                      </p>
                    </div>
                  </div>
                  
                  <div className='flex justify-end'>
                    <div className='bg-blue-600 rounded-lg p-4 max-w-[80%]'>
                      <p className='text-white'>
                        Hello! Can you help me understand what you can do?
                      </p>
                    </div>
                  </div>
                  
                  <div className='flex justify-start'>
                    <div className='bg-blue-800/30 rounded-lg p-4 max-w-[80%]'>
                      <p className='text-blue-100'>
                        Absolutely! I can help with coding, research, system diagnostics, 
                        and much more. I have access to various tools and can provide 
                        detailed assistance with your projects.
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Input Area */}
              <div className='p-4 border-t border-blue-800/30'>
                <div className='flex items-center gap-3'>
                  <div className='flex-1 relative'>
                    <input
                      type='text'
                      placeholder='Send a message...'
                      className='w-full bg-blue-900/50 border border-blue-700 rounded-lg px-4 py-3 text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'
                    />
                  </div>
                  <div className='flex items-center gap-2'>
                    <select className='bg-blue-800/50 border border-blue-700 rounded-lg px-3 py-2 text-blue-100 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500'>
                      <option>athena:7b</option>
                      <option>qwen2.5:7b</option>
                      <option>llama3:8b</option>
                    </select>
                    <button className='bg-blue-600 hover:bg-blue-700 rounded-lg p-3 transition-colors'>
                      <svg className='w-5 h-5 text-white' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
                        <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M12 19l9 2-9-18-9 18 9-2zm0 0v-8' />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </>
        )}
        {step === Step.CLI && (
          <>
            <div className='mx-auto flex flex-col space-y-28 text-center'>
              <h1 className='mt-4 text-3xl font-bold tracking-tight bg-gradient-to-r from-slate-800 via-blue-700 to-indigo-600 bg-clip-text text-transparent'>Athena Command Line</h1>
              <div className='mx-auto space-y-6'>
                <pre className='mx-auto text-3xl font-mono text-slate-500'>&gt; athena</pre>
                <p className='text-base text-slate-600'>Use Athena from the command line with advanced capabilities</p>
                <div className='flex items-center justify-center space-x-3'>
                  <code className='bg-white/80 backdrop-blur-sm px-4 py-3 rounded-xl text-sm font-mono border border-slate-200 shadow-lg'>
                    {command}
                  </code>
                  <button
                    onClick={() => {
                      copy(command)
                      setCommandCopied(true)
                      setTimeout(() => setCommandCopied(false), 2000)
                    }}
                    className='no-drag p-3 hover:bg-white/80 rounded-xl transition-all duration-200 shadow-md hover:shadow-lg'
                  >
                    {commandCopied ? (
                      <CheckIcon className='w-5 h-5 text-emerald-600' />
                    ) : (
                      <DocumentDuplicateIcon className='w-5 h-5 text-slate-500' />
                    )}
                  </button>
                </div>
              </div>
              <button
                onClick={() => setStep(Step.CAPABILITIES)}
                className='no-drag rounded-dm mx-auto w-[40%] rounded-xl bg-gradient-to-r from-slate-700 via-blue-600 to-indigo-600 px-6 py-3 text-sm font-semibold text-white hover:brightness-110 shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-0.5'
              >
                Next
              </button>
            </div>
          </>
        )}
        {step === Step.CAPABILITIES && (
          <>
            <div className='mx-auto flex flex-col space-y-12 text-center'>
              <h1 className='mt-4 text-3xl font-bold tracking-tight bg-gradient-to-r from-slate-800 via-blue-700 to-indigo-600 bg-clip-text text-transparent'>Athena Capabilities</h1>
              <div className='grid grid-cols-2 gap-8 max-w-3xl mx-auto'>
                <div className='bg-white/90 backdrop-blur-sm p-8 rounded-2xl shadow-xl border border-slate-200/50 hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1'>
                  <div className='flex items-center justify-center mb-4'>
                    <div className='w-16 h-16 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-2xl flex items-center justify-center shadow-lg'>
                      <SparklesIcon className='w-8 h-8 text-white drop-shadow-sm' />
                    </div>
                  </div>
                  <h3 className='font-bold text-slate-800 mb-3 text-lg'>Web Search</h3>
                  <p className='text-sm text-slate-600 leading-relaxed'>Real-time web search with DuckDuckGo and arXiv</p>
                </div>
                <div className='bg-white/90 backdrop-blur-sm p-8 rounded-2xl shadow-xl border border-slate-200/50 hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1'>
                  <div className='flex items-center justify-center mb-4'>
                    <div className='w-16 h-16 bg-gradient-to-br from-emerald-500 to-teal-500 rounded-2xl flex items-center justify-center shadow-lg'>
                      <CodeBracketIcon className='w-8 h-8 text-white drop-shadow-sm' />
                    </div>
                  </div>
                  <h3 className='font-bold text-slate-800 mb-3 text-lg'>Coding</h3>
                  <p className='text-sm text-slate-600 leading-relaxed'>MLX-powered coding assistance for Apple Silicon</p>
                </div>
                <div className='bg-white/90 backdrop-blur-sm p-8 rounded-2xl shadow-xl border border-slate-200/50 hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1'>
                  <div className='flex items-center justify-center mb-4'>
                    <div className='w-16 h-16 bg-gradient-to-br from-violet-500 to-purple-500 rounded-2xl flex items-center justify-center shadow-lg'>
                      <EyeIcon className='w-8 h-8 text-white drop-shadow-sm' />
                    </div>
                  </div>
                  <h3 className='font-bold text-slate-800 mb-3 text-lg'>Vision</h3>
                  <p className='text-sm text-slate-600 leading-relaxed'>Image analysis with FastVLM</p>
                </div>
                <div className='bg-white/90 backdrop-blur-sm p-8 rounded-2xl shadow-xl border border-slate-200/50 hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1'>
                  <div className='flex items-center justify-center mb-4'>
                    <div className='w-16 h-16 bg-gradient-to-br from-amber-500 to-orange-500 rounded-2xl flex items-center justify-center shadow-lg'>
                      <SpeakerWaveIcon className='w-8 h-8 text-white drop-shadow-sm' />
                    </div>
                  </div>
                  <h3 className='font-bold text-slate-800 mb-3 text-lg'>Voice</h3>
                  <p className='text-sm text-slate-600 leading-relaxed'>Text-to-speech with Kokoro</p>
                </div>
              </div>
              <button
                onClick={() => setStep(Step.FINISH)}
                className='no-drag rounded-dm mx-auto w-[40%] rounded-xl bg-gradient-to-r from-slate-700 via-blue-600 to-indigo-600 px-6 py-3 text-sm font-semibold text-white hover:brightness-110 shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-0.5'
              >
                Finish Setup
              </button>
            </div>
          </>
        )}
        {step === Step.FINISH && (
          <>
            <div className='mx-auto flex flex-col space-y-12 text-center'>
              <h1 className='mt-4 text-3xl font-bold tracking-tight bg-gradient-to-r from-slate-800 via-blue-700 to-indigo-600 bg-clip-text text-transparent'>Athena is Ready!</h1>
              <div className='bg-white/90 backdrop-blur-sm p-10 rounded-3xl shadow-2xl border border-slate-200/50 max-w-lg mx-auto'>
                <div className='flex items-center justify-center mb-6'>
                  <div className='w-20 h-20 bg-gradient-to-br from-emerald-500 via-blue-500 to-indigo-600 rounded-3xl flex items-center justify-center shadow-xl ring-4 ring-white/50'>
                    <SparklesIcon className='w-10 h-10 text-white drop-shadow-lg' />
                  </div>
                </div>
                <h3 className='font-bold text-slate-800 mb-4 text-xl'>Your Personal AI Assistant</h3>
                <p className='text-sm text-slate-600 mb-6 leading-relaxed'>
                  Athena is now configured with all your models and capabilities. 
                  Use the command line or web interface to interact with your AI.
                </p>
                <div className='space-y-3 text-xs text-slate-500 bg-slate-50/80 p-4 rounded-xl border border-slate-200/50'>
                  <p className='flex items-center justify-between'>
                    <span>Web Search:</span>
                    <code className='bg-white px-2 py-1 rounded text-slate-700 font-mono'>athena search "query"</code>
                  </p>
                  <p className='flex items-center justify-between'>
                    <span>Coding:</span>
                    <code className='bg-white px-2 py-1 rounded text-slate-700 font-mono'>athena code "function"</code>
                  </p>
                  <p className='flex items-center justify-between'>
                    <span>Chat:</span>
                    <code className='bg-white px-2 py-1 rounded text-slate-700 font-mono'>athena chat qwen2.5:7b</code>
                  </p>
                  <p className='flex items-center justify-between'>
                    <span>Vision:</span>
                    <code className='bg-white px-2 py-1 rounded text-slate-700 font-mono'>athena vision "describe"</code>
                  </p>
                </div>
              </div>
              <button
                onClick={() => {
                  store.set('first-time-run', true)
                  getCurrentWindow().close()
                }}
                className='no-drag rounded-dm mx-auto w-[40%] rounded-xl bg-gradient-to-r from-slate-700 via-blue-600 to-indigo-600 px-6 py-3 text-sm font-semibold text-white hover:brightness-110 shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-0.5'
              >
                Start Using Athena
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}