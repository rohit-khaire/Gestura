import { toast } from "react-hot-toast";

const ClosableToast = (message, type = "blank") => {
  return toast[type]((t) => (
    <div className="flex items-center justify-between w-full">
      <span>{message}</span>
      <button
        onClick={() => toast.dismiss(t.id)}
        className="ml-4 cursor-pointer  text-gray-300 hover:text-black "
      >
        ✖
      </button>
    </div>
  ));
};

export default ClosableToast;
