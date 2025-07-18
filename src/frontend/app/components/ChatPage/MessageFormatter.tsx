import React from 'react';

interface MessageFormatterProps {
  content: string;
  role: 'user' | 'assistant';
}

const MessageFormatter: React.FC<MessageFormatterProps> = ({ content, role }) => {
  if (role === 'user') {
    return (
      <div className="text-lg leading-relaxed">
        {content}
      </div>
    );
  }

  // Format assistant messages
  const formatAssistantMessage = (text: string) => {
    const lines = text.split('\n');
    const formattedElements: React.ReactNode[] = [];
    let currentIndex = 0;

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      
      if (!line) {
        formattedElements.push(<br key={currentIndex++} />);
        continue;
      }

      // Headers (lines that end with :)
      if (line.endsWith(':') && line.length > 3 && !line.includes('http')) {
        formattedElements.push(
          <h3 key={currentIndex++} className="font-semibold text-xl mt-4 mb-2 text-white">
            {line}
          </h3>
        );
      }
      // Numbered lists (1. 2. 3.)
      else if (/^\d+\.\s/.test(line)) {
        const content = line.replace(/^\d+\.\s/, '');
        const processedContent = content.replace(/\*\*(.*?)\*\*/g, '$1');
        formattedElements.push(
          <div key={currentIndex++} className="ml-4 mb-2">
            <span className="font-medium text-blue-300">{line.match(/^\d+\./)?.[0]}</span>
            <span className="ml-2 font-semibold">{processedContent}</span>
          </div>
        );
      }
      // Bullet points (- or *)
      else if (/^[-*]\s/.test(line)) {
        formattedElements.push(
          <div key={currentIndex++} className="ml-4 mb-2 flex items-start">
            <span className="text-blue-300 mr-2 mt-1">•</span>
            <span>{line.replace(/^[-*]\s/, '')}</span>
          </div>
        );
      }
      // Sub-bullet points (  - or   *)
      else if (/^\s{2,}[-*]\s/.test(line)) {
        formattedElements.push(
          <div key={currentIndex++} className="ml-8 mb-1 flex items-start">
            <span className="text-blue-300 mr-2 mt-1">◦</span>
            <span>{line.replace(/^\s*[-*]\s/, '')}</span>
          </div>
        );
      }
      // Bold text (**text**) - remove stars and make bold
      else if (line.includes('**')) {
        const parts = line.split(/(\*\*.*?\*\*)/);
        formattedElements.push(
          <p key={currentIndex++} className="mb-2 leading-relaxed">
            {parts.map((part, index) => 
              part.startsWith('**') && part.endsWith('**') ? (
                <strong key={index} className="font-semibold text-white">
                  {part.slice(2, -2)}
                </strong>
              ) : (
                <span key={index}>{part}</span>
              )
            )}
          </p>
        );
      }
      // Regular paragraphs
      else {
        formattedElements.push(
          <p key={currentIndex++} className="mb-2 leading-relaxed">
            {line}
          </p>
        );
      }
    }

    return formattedElements;
  };

  return (
    <div className="text-lg leading-relaxed">
      {formatAssistantMessage(content)}
    </div>
  );
};

export default MessageFormatter;