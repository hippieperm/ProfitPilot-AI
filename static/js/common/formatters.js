const formatters = {
    number: new Intl.NumberFormat('ko-KR'),
    currency: new Intl.NumberFormat('ko-KR', {
        style: 'currency',
        currency: 'KRW',
        maximumFractionDigits: 0
    }),
    percent: new Intl.NumberFormat('ko-KR', {
        style: 'percent',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    })
};

export function formatCurrency(value) {
    return formatters.currency.format(value);
}

export function formatNumber(value) {
    return formatters.number.format(value);
}

export function formatPercentage(value) {
    return formatters.percent.format(value / 100);
} 