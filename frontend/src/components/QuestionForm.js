import React from "react";
import { Button } from "react-bootstrap";
import { compose, withState } from 'recompose';
import * as R from 'ramda';

import { AnswerField } from "./AnswerField";
import { QuestionField } from "./Question";
import InputField from './InputField';
import "./AnswerField.css";
import "./QuestionForm.css";

const getEmptyQuestion = () => ({
  questionText: '',
  answers: [
    {answerText: '', correct: false},
    {answerText: '', correct: false},
    {answerText: '', correct: false}
  ],
  // Does question contain text?
  questionValid: false,
  isPublic: true
});

const Answers = ({ answers, setAnswers, removeAnswer }) => (
  <div className="answers" style={{ marginBottom: 20 }}>
    {answers.map(({ answerText, correct }, index) => (
      <AnswerField
        onChange={e => {
          const clonedAnswers = R.clone(answers);
          clonedAnswers[index].answerText = e.target.value;
          setAnswers(clonedAnswers);
        }}
        key={index}
        value={answers[index].answerText}
        label={`${(10 + index).toString(36)}. `}
        isCorrect={answers[index].correct}
        setIsCorrect={correct => {
          const clonedAnswers = R.clone(answers);
          clonedAnswers[index].correct = correct;
          setAnswers(clonedAnswers);
        }}
      />
    ))}

    <Button
      id = "addAnswerButton"
      bsStyle='info'
      onClick={() => setAnswers(
        [...answers, {answerText: '', correct: false}]
      )}
    >
      Add Answer
    </Button>
    <Button
      id = "addAnswerButton"
      bsStyle='info'
      onClick={() => {
        const newAnswers= R.remove(answers.length-1, 1, answers);
        setAnswers(newAnswers);
      }}
    >
      Remove Answer
    </Button>
  </div>
);

// Tests if given input has text
const answerHasText = (answer) => {
  return answer.answerText !== '';
};

const handleSubmit = state => {
  // Validate username is provided
  if (!state.username || state.username.trim() === '') {
    return alert("Username is required");
  }

  // An array of boolean values stating whether or not each answer has text
  const answersValid = state.questions.reduce(
    (acc, { questionValid, answers }) => acc && questionValid && !answers.find(answer => !answerHasText(answer)),
    true
  );

  if(!answersValid) {
    return alert("All fields are required");
  }

  // Check for duplicates before submission
  fetch(
    './check_duplicates',
    {
      method: 'POST',
      body: JSON.stringify({
        username: state.username,
        questions: state.questions.map(q => q.questionText)
      }),
      headers: {
        'Content-Type': 'application/json'
      },
    }
  )
    .then(res => res.json())
    .then(duplicateInfo => {
      // Get indices of duplicate questions
      const duplicateIndices = duplicateInfo.duplicates || [];
      
      // Proceed with submission anyway
      fetch(
        './store_questions',
        {
          method: 'POST',
          body: JSON.stringify(state),
          headers: {
            'Content-Type': 'application/json'
          },
        }
      )
        .then(res => res.json())
        .then(res => {
          let message = res.message + '\n\n';
          
          if (duplicateIndices.length > 0) {
            const duplicateNumbers = duplicateIndices.map(i => i + 1).join(', ');
            message += `Questions ${duplicateNumbers} were duplicates and skipped.\n`;
            const importedCount = state.questions.length - duplicateIndices.length;
            message += `${importedCount} new questions were imported.`;
          } else {
            message += `All ${state.questions.length} questions were imported successfully.`;
          }
          
          alert(message);
        });
    })
    .catch(err => {
      console.error('Error checking duplicates:', err);
      alert("Error checking duplicates");
    });
};

const Question = ({ state, setState }) => (
  <div style={{ paddingBottom: 25 }}>
    <QuestionField
      label="Question: "
      name='question'
      id='question'
      value={state.questionText}
      // Changes question state and questionValid state
      onChange={e => setState({ ...state, questionText: e.target.value, questionValid: true })}
    />

    <div style={{ width: 500, marginLeft: 20, paddingTop: 15 }}>
      <InputField label='Visibility:'>
        <label style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <input
            type="radio"
            name="visibility"
            value="public"
            checked={state.isPublic === true}
            onChange={() => setState({ ...state, isPublic: true })}
            style={{ marginRight: '5px' }}
          />
          Public
        </label>
        <label style={{ display: 'flex', alignItems: 'center', gap: '10px', marginTop: '8px' }}>
          <input
            type="radio"
            name="visibility"
            value="private"
            checked={state.isPublic === false}
            onChange={() => setState({ ...state, isPublic: false })}
            style={{ marginRight: '5px' }}
          />
          Private (xem dc khi nhap dung username)
        </label>
      </InputField>
    </div>

    <div style={{ width: 500, marginLeft: 20, paddingTop: 25 }}>
      <Answers
        answers={state.answers}
        setAnswers={newAnswers => setState({ ...state, answers: newAnswers })}
      />
    </div>
  </div>
);

const FormControls = ({ state, setState }) => (
  <div>
    <div style={{ paddingBottom: 25 }}>
      <InputField label='Username (required):'>
        <input class='infoInput' id='username'
          type='text'
          required
          value={state.username || ''}
          onChange={e => setState({ ...state, username: e.target.value })}
          placeholder="Enter your username"
        />
      </InputField>

      <InputField label='Topic / Tag:'>
        <input class='infoInput' id='topic'
          type='text'
          value={state.topic || ''}
          onChange={e => setState({ ...state, topic: e.target.value })}
        />
      </InputField>
    </div>

    <div style={{ flexDirection: "row" }}>
      <Button
        id="submitButton"
        bsStyle="primary"
        onClick={() => setState({...state, questions: R.append(getEmptyQuestion(), state.questions) })}
        style={{ marginTop: 0, marginRight: 10 }}
      >
        Add Question
      </Button>
      <Button
        id="submitButton"
        bsStyle="primary"
        onClick={() => {
          const newQuestions = R.remove(state.questions.length-1, 1, state.questions);
          setState({...state, questions: newQuestions});
        }}
        style={{ marginTop: 0, marginRight: 10 }}
      >
        Remove Question
      </Button>

      <Button
        id="submitButton"
        bsStyle="primary"
        onClick={() => handleSubmit(state)}
      >
        Submit
      </Button>
    </div>
  </div>
);

const Form = ({ state, setState }) => (
  <div className="form" style={{ width: 520, marginLeft: 20 }}>
    <form>
      <div>
        {state.questions.map((questionState, i) => (
          <Question
            key={i}
            state={questionState}
            setState={newState => setState({...state, questions: R.update(i, newState, state.questions) })}
          />
        ))}
      </div>

      <hr />

      <FormControls state={state} setState={setState} />
    </form>
  </div>
);

const initialState = {
  username: null,
  questions: [getEmptyQuestion()],
};

export default compose(
  withState('state', 'setState', initialState),
)(Form);
