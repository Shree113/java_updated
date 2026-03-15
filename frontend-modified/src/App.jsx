import React from 'react'
import { Routes, Route } from 'react-router-dom'
import Welcome from './pages/Welcome'
import Instructions from './pages/Instructions'
import Quiz from './pages/Quiz'
import ThankYou from './pages/ThankYou'
import StudentEntry from './pages/StudentEntry'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Welcome />} />
      <Route path="/student-entry" element={<StudentEntry />} />
      <Route path="/instructions" element={<Instructions />} />
      <Route path="/quiz" element={<Quiz />} />
      <Route path="/thank-you" element={<ThankYou />} />
    </Routes>
  )
}

export default App
