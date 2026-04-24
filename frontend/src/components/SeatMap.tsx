import type { Seat } from "../types";

type Props = {
  seats: Seat[];
  selected: string[];
  onToggle: (seat: Seat) => void;
};

export default function SeatMap({ seats, selected, onToggle }: Props) {
  const rows = seats.reduce<Record<string, Seat[]>>((acc, seat) => {
    acc[seat.row] = [...(acc[seat.row] ?? []), seat];
    return acc;
  }, {});

  return (
    <div className="seat-map">
      <div className="screen">Screen</div>
      <div className="seat-rows">
        {Object.entries(rows).map(([row, rowSeats]) => (
          <div className="seat-row" key={row}>
            <span className="row-label">{row}</span>
            <div className="seat-grid" style={{ gridTemplateColumns: `repeat(${rowSeats.length}, minmax(28px, 1fr))` }}>
              {rowSeats.map((seat) => {
                const isSelected = selected.includes(seat.seatId);
                const disabled = seat.status !== "AVAILABLE";
                return (
                  <button
                    key={seat.seatId}
                    className={`seat ${seat.status.toLowerCase()} ${seat.type.toLowerCase()} ${isSelected ? "selected" : ""}`}
                    type="button"
                    disabled={disabled}
                    onClick={() => onToggle(seat)}
                    title={`${seat.row}${seat.number} ${seat.type.toLowerCase()} ${seat.status.toLowerCase()}`}
                  >
                    {seat.number}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>
      <div className="seat-legend">
        <span><i className="seat available" /> Available</span>
        <span><i className="seat selected" /> Selected</span>
        <span><i className="seat held" /> Held</span>
        <span><i className="seat booked" /> Booked</span>
        <span><i className="seat premium" /> Premium</span>
      </div>
    </div>
  );
}
