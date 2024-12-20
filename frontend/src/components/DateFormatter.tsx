export const DateFormatter = ({ dateString }: { dateString: string }) => {
    const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    
    // Check if the date is valid
    if (isNaN(date.getTime())) {
      return 'Invalid Date';
    }

    const options: Intl.DateTimeFormatOptions = { 
        year: '2-digit', 
        month: '2-digit', 
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        //second: '2-digit',
        timeZoneName: 'short'
      };

    return date.toLocaleString('en-US', options);
  };

  return (
    <div>
      <p>{formatDate(dateString)}</p>
    </div>
  );
};
