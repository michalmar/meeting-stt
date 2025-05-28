import React from "react";

interface AnalysisResultProps {
  analysisResult: string;
}

const AnalysisResultDisplay: React.FC<AnalysisResultProps> = ({ analysisResult }) => {
  let data;
  try {
    data = JSON.parse(analysisResult);
  } catch (e) {
    return <div>Invalid analysis result format.</div>;
  }

  return (
    <div>
      <h3>Analysis Result</h3>
      <ul>
        <li>
          <strong>Customer Issue:</strong> {data.customer_issue}
        </li>
        <li>
          <strong>Agent Response Approach:</strong> {data.agent_response_approach}
        </li>
        <li>
          <strong>Tone and Sentiment:</strong>
          <ul>
            <li>
              <strong>Customer:</strong> {data.tone_and_sentiment?.customer}
            </li>
            <li>
              <strong>Agent:</strong> {data.tone_and_sentiment?.agent}
            </li>
          </ul>
        </li>
        <li>
          <strong>Issue Resolution:</strong> {data.issue_resolution}
        </li>
        <li>
          <strong>Improvement Suggestions:</strong>
          <ul>
            {data.improvement_suggestions
              ? data.improvement_suggestions
                  .split(/\d+\.\s/)
                  .filter(Boolean)
                  .map((s: string, i: number) => <li key={i}>{s.trim()}</li>)
              : null}
          </ul>
        </li>
      </ul>
    </div>
  );
};

export default AnalysisResultDisplay;
