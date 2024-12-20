import React, { useState, useEffect } from "react";
import { api } from "../services/api";
import { AxiosProgressEvent } from "axios";

const NumberDisplay: React.FC = () => {
  const [numbers, setNumbers] = useState<number[]>([]);

  useEffect(() => {
    let data = "";
    const fetchNumbers = async () => {
      try {
        const response = await api.get("/stream", {
          responseType: "text",
          onDownloadProgress: (progressEvent: AxiosProgressEvent) => {
            if (progressEvent.event?.target instanceof XMLHttpRequest) {
              const newData = progressEvent.event.target.responseText;
              const newContent = newData.substring(data.length);
              data = newData;

              const lines = newContent.split("\n\n");
              lines.forEach((line: string) => {
                if (line.startsWith("data: ")) {
                  const number = parseInt(line.substring(6), 10);
                  if (!isNaN(number)) {
                    setNumbers((prevNumbers) => [...prevNumbers, number]);
                  }
                }
              });
            }
          },
        });

        // Handle any final processing if needed
        console.log("Stream completed", response);
      } catch (error) {
        console.error("Error fetching numbers:", error);
      }
    };

    fetchNumbers();

    return () => {
      // If needed, you can add cleanup logic here
    };
  }, []);

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Streamed Numbers</h1>
      <div className="flex flex-wrap gap-2">
        {numbers.map((number, index) => (
          <span
            key={index}
            className="bg-blue-500 text-white px-2 py-1 rounded"
          >
            {number}
          </span>
        ))}
      </div>
    </div>
  );
};

export default NumberDisplay;
